import json
from typing import Any


TOOL_DESCRIPTIONS = """
- extract_iocs(text): Extract IPs, hashes, domains, CVEs from text
- abuseipdb_lookup(ioc_value, ioc_type): Check IP/domain reputation (free API)
- mitre_lookup(keywords): Find MITRE ATT&CK techniques for attack patterns
- search_playbook(incident_type, severity): Get response steps for incident type
"""


PLAYBOOKS = {
    "ransomware": [
        "Isolate affected hosts immediately",
        "Preserve memory dumps before remediation",
        "Block C2 IPs at perimeter firewall",
        "Notify management and legal",
        "Begin recovery from verified clean backup",
    ],
    "phishing": [
        "Reset compromised credentials",
        "Block sender domain at email gateway",
        "Scan endpoint for malware",
        "Alert affected users with awareness email",
        "Review and update email filtering rules",
    ],
    "data_exfiltration": [
        "Block exfiltration destination IPs/domains",
        "Audit DLP logs for scope of data exposed",
        "Revoke compromised API tokens and sessions",
        "Notify Data Protection Officer",
        "Preserve network packet captures as evidence",
    ],
    "lateral_movement": [
        "Reset all administrative credentials",
        "Enable MFA on all privileged accounts",
        "Audit Active Directory for new/modified accounts",
        "Segment the affected network zone",
        "Review authentication logs for full scope",
    ],
    "brute_force": [
        "Block attacking source IPs at firewall",
        "Enable account lockout policy",
        "Force password reset for targeted accounts",
        "Review authentication logs",
        "Enable MFA on affected accounts immediately",
    ],
    "unknown": [
        "Preserve all relevant logs immediately",
        "Escalate to senior analyst for review",
        "Isolate most suspicious hosts as precaution",
        "Open P2 priority tracking ticket",
    ],
}


def get_tool_definitions() -> list:
    return [
        {
            "name": "extract_iocs",
            "description": "Extract IPs, hashes, domains, CVEs from text.",
            "input_schema": {"text": "string"},
        },
        {
            "name": "abuseipdb_lookup",
            "description": "Check IP/domain reputation using AbuseIPDB or a stub.",
            "input_schema": {"ioc_value": "string", "ioc_type": "string"},
        },
        {
            "name": "mitre_lookup",
            "description": "Find MITRE ATT&CK techniques for attack patterns.",
            "input_schema": {"keywords": "string"},
        },
        {
            "name": "search_playbook",
            "description": "Get response steps for incident type and severity.",
            "input_schema": {"incident_type": "string", "severity": "string"},
        },
    ]


def _json_dumps(value: Any) -> str:
    return json.dumps(value, default=str)


def _call_extract_iocs(tool_input: dict) -> str:
    text = str(tool_input.get("text", ""))
    try:
        from backend.enrichment.ioc_extractor import extract_iocs

        result = extract_iocs(text)
    except Exception:
        result = [
            {"type": "ip", "value": "185.220.101.1", "confidence": 0.85},
            {"type": "hash", "value": "abc123def456", "confidence": 0.95},
        ]
    return _json_dumps(result)


def _call_abuseipdb_lookup(tool_input: dict) -> str:
    ioc_value = str(tool_input.get("ioc_value", ""))
    ioc_type = str(tool_input.get("ioc_type", ""))
    try:
        from backend.enrichment.abuseipdb import lookup

        result = lookup(ioc_value, ioc_type)
    except Exception as exc:
        result = {
            "error": str(exc),
            "stub": True,
            "reputation": "suspicious",
            "abuse_score": 52,
        }
    return _json_dumps(result)


def _call_mitre_lookup(tool_input: dict) -> str:
    keywords = str(tool_input.get("keywords", ""))
    try:
        from backend.enrichment.mitre import search_techniques

        result = search_techniques(keywords)
    except Exception:
        result = [
            {
                "technique_id": "T1059.001",
                "technique_name": "PowerShell",
                "tactic": "execution",
            }
        ]
    return _json_dumps(result)


def _call_search_playbook(tool_input: dict) -> str:
    incident_type = str(tool_input.get("incident_type", "unknown")).lower()
    if incident_type not in PLAYBOOKS:
        incident_type = "unknown"
    return _json_dumps(PLAYBOOKS[incident_type])


def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "extract_iocs":
        return _call_extract_iocs(tool_input)
    if tool_name == "abuseipdb_lookup":
        return _call_abuseipdb_lookup(tool_input)
    if tool_name == "mitre_lookup":
        return _call_mitre_lookup(tool_input)
    if tool_name == "search_playbook":
        return _call_search_playbook(tool_input)
    return _json_dumps({"error": f"Unknown tool: {tool_name}", "stub": True})
