TECHNIQUE_MAP = {
    "powershell": [
        {
            "technique_id": "T1059.001",
            "technique_name": "PowerShell",
            "tactic": "execution",
        }
    ],
    "phishing": [
        {
            "technique_id": "T1566.001",
            "technique_name": "Spearphishing Attachment",
            "tactic": "initial_access",
        }
    ],
    "credential": [
        {
            "technique_id": "T1078",
            "technique_name": "Valid Accounts",
            "tactic": "defense_evasion",
        }
    ],
    "brute force": [
        {
            "technique_id": "T1110",
            "technique_name": "Brute Force",
            "tactic": "credential_access",
        }
    ],
    "brute_force": [
        {
            "technique_id": "T1110",
            "technique_name": "Brute Force",
            "tactic": "credential_access",
        }
    ],
    "ssh": [
        {
            "technique_id": "T1021.004",
            "technique_name": "Remote Services: SSH",
            "tactic": "lateral_movement",
        }
    ],
    "ransomware": [
        {
            "technique_id": "T1486",
            "technique_name": "Data Encrypted for Impact",
            "tactic": "impact",
        }
    ],
    "encrypt": [
        {
            "technique_id": "T1486",
            "technique_name": "Data Encrypted for Impact",
            "tactic": "impact",
        }
    ],
    "exfiltration": [
        {
            "technique_id": "T1041",
            "technique_name": "Exfiltration Over C2 Channel",
            "tactic": "exfiltration",
        }
    ],
    "exfil": [
        {
            "technique_id": "T1041",
            "technique_name": "Exfiltration Over C2 Channel",
            "tactic": "exfiltration",
        }
    ],
    "lateral": [
        {
            "technique_id": "T1021",
            "technique_name": "Remote Services",
            "tactic": "lateral_movement",
        }
    ],
    "persistence": [
        {
            "technique_id": "T1053",
            "technique_name": "Scheduled Task/Job",
            "tactic": "persistence",
        }
    ],
    "discovery": [
        {
            "technique_id": "T1082",
            "technique_name": "System Information Discovery",
            "tactic": "discovery",
        }
    ],
    "dns": [
        {
            "technique_id": "T1071.004",
            "technique_name": "DNS",
            "tactic": "command_and_control",
        }
    ],
    "http": [
        {
            "technique_id": "T1071.001",
            "technique_name": "Web Protocols",
            "tactic": "command_and_control",
        }
    ],
    "registry": [
        {
            "technique_id": "T1112",
            "technique_name": "Modify Registry",
            "tactic": "defense_evasion",
        }
    ],
    "injection": [
        {
            "technique_id": "T1055",
            "technique_name": "Process Injection",
            "tactic": "privilege_escalation",
        }
    ],
    "mimikatz": [
        {
            "technique_id": "T1003",
            "technique_name": "OS Credential Dumping",
            "tactic": "credential_access",
        }
    ],
    "scheduled task": [
        {
            "technique_id": "T1053.005",
            "technique_name": "Scheduled Task",
            "tactic": "persistence",
        }
    ],
    "web shell": [
        {
            "technique_id": "T1505.003",
            "technique_name": "Web Shell",
            "tactic": "persistence",
        }
    ],
    "log4j": [
        {
            "technique_id": "T1190",
            "technique_name": "Exploit Public-Facing Application",
            "tactic": "initial_access",
        }
    ],
    "log4shell": [
        {
            "technique_id": "T1190",
            "technique_name": "Exploit Public-Facing Application",
            "tactic": "initial_access",
        }
    ],
    "cve-2021-44228": [
        {
            "technique_id": "T1190",
            "technique_name": "Exploit Public-Facing Application",
            "tactic": "initial_access",
        }
    ],
}


def search_techniques(keywords: str) -> list[dict]:
    keywords_lower = keywords.lower()
    words = [word.strip() for word in keywords_lower.replace(",", " ").split()]
    results = []
    seen_ids = set()

    for map_key, techniques in TECHNIQUE_MAP.items():
        if map_key in keywords_lower or any(word in map_key for word in words):
            for technique in techniques:
                if technique["technique_id"] not in seen_ids:
                    results.append(technique)
                    seen_ids.add(technique["technique_id"])

    if not results:
        results = [
            {
                "technique_id": "T0000",
                "technique_name": "Unknown Technique",
                "tactic": "unknown",
            }
        ]
    return results[:5]
