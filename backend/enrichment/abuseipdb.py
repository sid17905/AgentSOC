import os
from datetime import datetime


ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"
BAD_IP_PREFIXES = ["185.220.", "45.142.", "23.129.", "199.87.", "205.185."]
BAD_DOMAINS_TLD = {".tk", ".xyz", ".top", ".club", ".gq"}


def lookup(ioc_value: str, ioc_type: str) -> dict:
    api_key = os.getenv("ABUSEIPDB_API_KEY", "")
    checked_at = datetime.utcnow().isoformat() + "Z"

    if not api_key:
        reputation = _offline_reputation(ioc_value, ioc_type)
        return {
            "ioc": ioc_value,
            "type": ioc_type,
            "abuse_score": 0,
            "total_reports": 0,
            "country_code": None,
            "reputation": reputation,
            "last_reported": None,
            "checked_at": checked_at,
            "error": "No API key — using offline list",
        }

    if ioc_type not in ("ip",):
        return {
            "ioc": ioc_value,
            "type": ioc_type,
            "abuse_score": 0,
            "total_reports": 0,
            "country_code": None,
            "reputation": _offline_reputation(ioc_value, ioc_type),
            "last_reported": None,
            "checked_at": checked_at,
            "error": f"AbuseIPDB does not support type '{ioc_type}'",
        }

    try:
        import requests

        resp = requests.get(
            ABUSEIPDB_URL,
            headers={"Key": api_key, "Accept": "application/json"},
            params={"ipAddress": ioc_value, "maxAgeInDays": 90},
            timeout=5,
        )
        if resp.status_code == 429:
            return _rate_limit_stub(ioc_value, ioc_type, checked_at)
        resp.raise_for_status()

        data = resp.json()["data"]
        score = data.get("abuseConfidenceScore", 0)
        if score >= 80:
            rep = "malicious"
        elif score >= 25:
            rep = "suspicious"
        else:
            rep = "clean"

        return {
            "ioc": ioc_value,
            "type": ioc_type,
            "abuse_score": score,
            "total_reports": data.get("totalReports", 0),
            "country_code": data.get("countryCode"),
            "reputation": rep,
            "last_reported": data.get("lastReportedAt"),
            "checked_at": checked_at,
            "error": None,
        }
    except Exception as e:
        return {
            "ioc": ioc_value,
            "type": ioc_type,
            "abuse_score": 0,
            "total_reports": 0,
            "country_code": None,
            "reputation": "unknown",
            "last_reported": None,
            "checked_at": checked_at,
            "error": str(e),
        }


def _offline_reputation(value: str, ioc_type: str) -> str:
    if ioc_type == "ip":
        if any(value.startswith(prefix) for prefix in BAD_IP_PREFIXES):
            return "suspicious"
        return "unknown"
    if ioc_type == "domain":
        if any(value.endswith(tld) for tld in BAD_DOMAINS_TLD):
            return "suspicious"
        return "unknown"
    return "unknown"


def _rate_limit_stub(value, itype, ts):
    return {
        "ioc": value,
        "type": itype,
        "abuse_score": 0,
        "total_reports": 0,
        "country_code": None,
        "reputation": "unknown",
        "last_reported": None,
        "checked_at": ts,
        "error": "Rate limit — retry later",
    }
