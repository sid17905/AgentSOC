import json
import re
import xml.etree.ElementTree as ET
from typing import Any

from backend.config import utc_now

IP_PATTERN = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
HASH_PATTERN = r'\b[a-fA-F0-9]{32,64}\b'
CVE_PATTERN = r'CVE-\d{4}-\d{4,7}'
TIMESTAMP_PAT = r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}'

SYSLOG_PATTERN = (
    r'^(?P<timestamp>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
    r'\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'
    r'(?P<hostname>\S+)\s+'
    r'(?P<process>[^:\[\s]+)(?:\[\d+\])?:?\s*'
    r'(?P<message>.*)$'
)

_SYSLOG_RE = re.compile(SYSLOG_PATTERN)
_TIMESTAMP_RE = re.compile(TIMESTAMP_PAT)
_IP_RE = re.compile(IP_PATTERN)
_HASH_RE = re.compile(HASH_PATTERN)
_CVE_RE = re.compile(CVE_PATTERN)
_ACTION_RE = re.compile(
    r'\b('
    r'allow(?:ed)?|accept(?:ed)?|deny|denied|block(?:ed)?|drop(?:ped)?|'
    r'reject(?:ed)?|login|logon|logout|failed|failure|success|detected|'
    r'quarantine(?:d)?|created|deleted|modified|alert|connect(?:ed|ion)?|'
    r'disconnect(?:ed)?'
    r')\b',
    re.IGNORECASE,
)
_SEVERITY_RE = re.compile(
    r'\b(P[1-4]|critical|high|medium|low|info|informational|warning|warn|'
    r'error|notice|debug)\b',
    re.IGNORECASE,
)

_ENTRY_FIELDS = (
    "timestamp",
    "source_ip",
    "dest_ip",
    "hostname",
    "process",
    "action",
    "severity",
    "raw_line",
)


def parse_log(raw_text: str) -> dict:
    parsed_at = utc_now().isoformat()
    raw_text = raw_text if isinstance(raw_text, str) else str(raw_text)

    source_type = _detect_source_type(raw_text)
    if source_type == "siem_json":
        entries = _parse_siem_json(raw_text)
        if not entries:
            source_type = "raw"
            entries = _parse_raw_lines(raw_text, source_type)
    elif source_type == "windows_event":
        entries = _parse_windows_event_xml(raw_text)
        if not entries:
            entries = _parse_raw_lines(raw_text, source_type)
    elif source_type == "syslog":
        entries = _parse_syslog(raw_text)
    else:
        entries = _parse_raw_lines(raw_text, source_type)

    entry_count = len(entries)
    normalized_text = _build_normalized_text(
        parsed_at=parsed_at,
        entry_count=entry_count,
        source_type=source_type,
        entries=entries,
    )

    return {
        "source_type": source_type,
        "entries": entries,
        "entry_count": entry_count,
        "normalized_text": normalized_text,
        "parsed_at": parsed_at,
    }


def _detect_source_type(raw_text: str) -> str:
    stripped = raw_text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "siem_json"
    if "<Event>" in raw_text or "<Event " in raw_text or "<Event\n" in raw_text:
        return "windows_event"

    first_line = _first_non_empty_line(raw_text)
    if first_line and _SYSLOG_RE.match(first_line):
        return "syslog"

    return "raw"


def _parse_siem_json(raw_text: str) -> list[dict]:
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return []

    records = _json_records(parsed)
    return [_entry_from_json_record(record) for record in records]


def _json_records(parsed: Any) -> list[Any]:
    if isinstance(parsed, list):
        return parsed

    if isinstance(parsed, dict):
        for key in ("events", "alerts", "entries", "logs", "records", "results"):
            value = parsed.get(key)
            if isinstance(value, list):
                return value
        return [parsed]

    return [parsed]


def _entry_from_json_record(record: Any) -> dict:
    raw_line = _json_raw_line(record)
    if not isinstance(record, dict):
        return _entry_from_line(raw_line)

    flat = _flatten_json(record)
    entry = _entry_from_line(raw_line)
    entry.update(
        {
            "timestamp": _first_value(
                flat,
                (
                    "timestamp",
                    "@timestamp",
                    "time",
                    "event_time",
                    "event.time",
                    "created_at",
                    "date",
                ),
            )
            or entry["timestamp"],
            "source_ip": _first_value(
                flat,
                (
                    "source_ip",
                    "src_ip",
                    "srcip",
                    "src",
                    "client_ip",
                    "clientip",
                    "source.ip",
                    "source.address",
                    "sourceip",
                ),
            )
            or entry["source_ip"],
            "dest_ip": _first_value(
                flat,
                (
                    "dest_ip",
                    "destination_ip",
                    "dst_ip",
                    "dstip",
                    "dst",
                    "dest",
                    "server_ip",
                    "destination.ip",
                    "destination.address",
                    "destinationip",
                ),
            )
            or entry["dest_ip"],
            "hostname": _first_value(
                flat,
                (
                    "hostname",
                    "host",
                    "host.name",
                    "computer",
                    "computer_name",
                    "device",
                    "machine",
                ),
            )
            or entry["hostname"],
            "process": _first_value(
                flat,
                (
                    "process",
                    "process_name",
                    "process.name",
                    "app",
                    "application",
                    "program",
                    "service",
                ),
            )
            or entry["process"],
            "action": _first_value(
                flat,
                (
                    "action",
                    "event_action",
                    "event.action",
                    "activity",
                    "outcome",
                    "result",
                    "status",
                    "event",
                ),
            )
            or entry["action"],
            "severity": _first_value(
                flat,
                (
                    "severity",
                    "level",
                    "priority",
                    "risk",
                    "risk_level",
                    "event.severity",
                ),
            )
            or entry["severity"],
        }
    )
    return _clean_entry(entry)


def _parse_windows_event_xml(raw_text: str) -> list[dict]:
    root = _parse_xml_root(raw_text)
    if root is None:
        return []

    events = _event_elements(root)
    return [_entry_from_windows_event(event) for event in events]


def _parse_xml_root(raw_text: str) -> ET.Element | None:
    for candidate in (raw_text, f"<Events>{raw_text}</Events>"):
        try:
            return ET.fromstring(candidate)
        except ET.ParseError:
            continue
    return None


def _event_elements(root: ET.Element) -> list[ET.Element]:
    if _tag_name(root.tag) == "Event":
        return [root]
    return [element for element in root.iter() if _tag_name(element.tag) == "Event"]


def _entry_from_windows_event(event: ET.Element) -> dict:
    raw_line = ET.tostring(event, encoding="unicode", short_empty_elements=True)
    entry = _entry_from_line(raw_line)
    event_data = _windows_event_data(event)

    event_id = _first_child_text(event, "EventID")
    provider = _first_element(event, "Provider")
    time_created = _first_element(event, "TimeCreated")

    timestamp = None
    if time_created is not None:
        timestamp = _as_text(time_created.attrib.get("SystemTime"))

    provider_name = None
    if provider is not None:
        provider_name = _as_text(provider.attrib.get("Name"))

    entry.update(
        {
            "timestamp": timestamp or entry["timestamp"],
            "source_ip": _first_value(
                event_data,
                (
                    "sourceip",
                    "sourceaddress",
                    "srcip",
                    "ipaddress",
                    "clientaddress",
                    "clientip",
                ),
            )
            or entry["source_ip"],
            "dest_ip": _first_value(
                event_data,
                ("destinationip", "destinationaddress", "destip", "dstip", "serverip"),
            )
            or entry["dest_ip"],
            "hostname": _first_child_text(event, "Computer")
            or _first_value(event_data, ("hostname", "computer", "computername"))
            or entry["hostname"],
            "process": _first_value(
                event_data,
                ("processname", "process", "image", "application", "app"),
            )
            or provider_name
            or entry["process"],
            "action": _first_value(event_data, ("action", "eventaction", "activity"))
            or (f"EventID {event_id}" if event_id else entry["action"]),
            "severity": _first_value(event_data, ("severity", "level"))
            or _first_child_text(event, "Level")
            or entry["severity"],
        }
    )
    return _clean_entry(entry)


def _windows_event_data(event: ET.Element) -> dict[str, str]:
    values = {}
    for element in event.iter():
        if _tag_name(element.tag) != "Data":
            continue
        name = _as_text(element.attrib.get("Name") or element.attrib.get("name"))
        value = _as_text(element.text)
        if name and value:
            values[name.lower()] = value
    return values


def _parse_syslog(raw_text: str) -> list[dict]:
    entries = []
    for line in _non_empty_lines(raw_text):
        match = _SYSLOG_RE.match(line)
        if not match:
            entries.append(_entry_from_line(line))
            continue

        entry = _entry_from_line(line)
        message = match.group("message")
        entry.update(
            {
                "timestamp": match.group("timestamp"),
                "hostname": match.group("hostname"),
                "process": match.group("process"),
                "action": _extract_action(message) or entry["action"],
                "severity": _extract_severity(message) or entry["severity"],
            }
        )
        entries.append(_clean_entry(entry))
    return entries


def _parse_raw_lines(raw_text: str, source_type: str) -> list[dict]:
    del source_type
    return [_entry_from_line(line) for line in _non_empty_lines(raw_text)]


def _entry_from_line(raw_line: str) -> dict:
    raw_line = raw_line if isinstance(raw_line, str) else str(raw_line)
    ips = _IP_RE.findall(raw_line)

    # Scan all required IOC patterns on every line, even though the shared entry
    # schema only exposes IP fields directly.
    _HASH_RE.findall(raw_line)
    _CVE_RE.findall(raw_line)

    return _clean_entry(
        {
            "timestamp": _extract_timestamp(raw_line),
            "source_ip": ips[0] if ips else None,
            "dest_ip": ips[1] if len(ips) > 1 else None,
            "hostname": None,
            "process": None,
            "action": _extract_action(raw_line),
            "severity": _extract_severity(raw_line),
            "raw_line": raw_line,
        }
    )


def _extract_timestamp(raw_line: str) -> str | None:
    match = _TIMESTAMP_RE.search(raw_line)
    return match.group(0) if match else None


def _extract_action(raw_line: str) -> str | None:
    match = _ACTION_RE.search(raw_line)
    return match.group(1).lower() if match else None


def _extract_severity(raw_line: str) -> str | None:
    match = _SEVERITY_RE.search(raw_line)
    if not match:
        return None
    value = match.group(1)
    return value.upper() if re.fullmatch(r'p[1-4]', value, re.IGNORECASE) else value.lower()


def _build_normalized_text(
    parsed_at: str,
    entry_count: int,
    source_type: str,
    entries: list[dict],
) -> str:
    notable = _notable_values(entries)
    return (
        f"Log analysis [{parsed_at}]: {entry_count} entries detected.\n"
        f"Source type: {source_type}.\n"
        f"Notable: {', '.join(notable) if notable else 'none'}"
    )


def _notable_values(entries: list[dict]) -> list[str]:
    seen = set()
    notable = []
    for entry in entries:
        for key in ("source_ip", "action"):
            value = entry.get(key)
            if value and value not in seen:
                seen.add(value)
                notable.append(value)
    return notable


def _flatten_json(value: Any, prefix: str = "") -> dict[str, str]:
    flat = {}
    if not isinstance(value, dict):
        return flat

    for key, child in value.items():
        key_text = str(key).lower()
        dotted_key = f"{prefix}.{key_text}" if prefix else key_text
        if isinstance(child, dict):
            flat.update(_flatten_json(child, dotted_key))
        else:
            child_text = _as_text(child)
            if child_text is not None:
                flat[dotted_key] = child_text
    return flat


def _first_value(values: dict[str, str], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = values.get(key)
        if value:
            return value
    return None


def _first_child_text(root: ET.Element, tag_name: str) -> str | None:
    element = _first_element(root, tag_name)
    return _as_text(element.text) if element is not None else None


def _first_element(root: ET.Element, tag_name: str) -> ET.Element | None:
    for element in root.iter():
        if _tag_name(element.tag) == tag_name:
            return element
    return None


def _tag_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _first_non_empty_line(raw_text: str) -> str | None:
    for line in raw_text.splitlines():
        if line.strip():
            return line.strip()
    return None


def _non_empty_lines(raw_text: str) -> list[str]:
    return [line for line in raw_text.splitlines() if line.strip()]


def _json_raw_line(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except TypeError:
        return str(value)


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


def _clean_entry(entry: dict) -> dict:
    cleaned = {field: entry.get(field) for field in _ENTRY_FIELDS}
    cleaned["raw_line"] = cleaned["raw_line"] or ""
    return cleaned
