from datetime import datetime

from backend.enrichment.ioc_extractor import extract_iocs
from backend.parsers.log_parser import parse_log


def test_parse_syslog():
    sample = "Jan 15 10:23:45 webserver sshd[1234]: Failed password for root from 192.168.1.50 port 22"
    result = parse_log(sample)
    assert result["source_type"] == "syslog"
    assert result["entry_count"] == 1
    assert "192.168.1.50" in result["normalized_text"]
    assert "parsed_at" in result
    datetime.fromisoformat(result["parsed_at"].rstrip("Z"))


def test_parse_json_siem():
    sample = '[{"timestamp":"2024-01-15","src_ip":"10.0.0.5","action":"DNS query","domain":"malicious.ru"}]'
    result = parse_log(sample)
    assert result["source_type"] == "siem_json"


def test_ioc_extraction_has_timestamps():
    text = "Connection from 185.220.101.1 hash abc123def456 CVE-2021-44228"
    iocs = extract_iocs(text)
    types = [i["type"] for i in iocs]
    assert "ip" in types
    assert "cve" in types
    for ioc in iocs:
        assert "extracted_at" in ioc
