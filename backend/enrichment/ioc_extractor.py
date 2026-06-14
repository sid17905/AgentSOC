import re
from datetime import datetime


IPV4_PATTERN = r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
MD5_PATTERN = r'\b[a-fA-F0-9]{32}\b'
SHA1_PATTERN = r'\b[a-fA-F0-9]{40}\b'
SHA256_PATTERN = r'\b[a-fA-F0-9]{64}\b'
CVE_PATTERN = r'CVE-\d{4}-\d{4,7}'
DOMAIN_PATTERN = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
URL_PATTERN = r'https?://[^\s"\'<>]+'

VALID_TLDS = {
    "com",
    "net",
    "org",
    "io",
    "ru",
    "cn",
    "tk",
    "xyz",
    "uk",
    "de",
    "edu",
    "gov",
    "mil",
    "co",
    "info",
    "biz",
    "us",
    "fr",
    "jp",
}


def extract_iocs(text: str) -> list[dict]:
    ts = datetime.utcnow().isoformat() + "Z"
    text = text if isinstance(text, str) else str(text)
    iocs = []
    seen_values = set()

    for value in re.findall(URL_PATTERN, text):
        _add_ioc(iocs, seen_values, "url", value, 0.80, ts)

    for value in re.findall(IPV4_PATTERN, text):
        confidence = 0.4 if is_private_ip(value) else 0.85
        _add_ioc(iocs, seen_values, "ip", value, confidence, ts)

    for value in re.findall(SHA256_PATTERN, text):
        _add_ioc(iocs, seen_values, "hash", value, 0.95, ts)

    for value in re.findall(SHA1_PATTERN, text):
        _add_ioc(iocs, seen_values, "hash", value, 0.95, ts)

    for value in re.findall(MD5_PATTERN, text):
        _add_ioc(iocs, seen_values, "hash", value, 0.95, ts)

    for value in re.findall(CVE_PATTERN, text):
        _add_ioc(iocs, seen_values, "cve", value, 0.99, ts)

    for value in re.findall(DOMAIN_PATTERN, text):
        domain = value.lower().rstrip(".")
        if not _has_valid_tld(domain):
            continue
        confidence = _domain_confidence(domain)
        _add_ioc(iocs, seen_values, "domain", domain, confidence, ts)

    return iocs


def is_private_ip(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False

    try:
        first, second = int(parts[0]), int(parts[1])
    except ValueError:
        return False

    return (
        first == 10
        or first == 127
        or (first == 172 and 16 <= second <= 31)
        or (first == 192 and second == 168)
    )


def _add_ioc(
    iocs: list[dict],
    seen_values: set[str],
    ioc_type: str,
    value: str,
    confidence: float,
    extracted_at: str,
) -> None:
    if value in seen_values:
        return

    seen_values.add(value)
    iocs.append(
        {
            "type": ioc_type,
            "value": value,
            "confidence": confidence,
            "extracted_at": extracted_at,
        }
    )


def _has_valid_tld(domain: str) -> bool:
    return domain.rsplit(".", 1)[-1] in VALID_TLDS


def _domain_confidence(domain: str) -> float:
    tld = domain.rsplit(".", 1)[-1]
    if tld in {"ru", "cn", "tk", "xyz"}:
        return 0.75
    if tld in {"com", "org", "net"}:
        return 0.50
    return 0.50
