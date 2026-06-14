def test_abuseipdb_stub():
    from backend.enrichment.abuseipdb import lookup

    result = lookup("1.2.3.4", "ip")
    assert "reputation" in result
    assert "abuse_score" in result
    assert "checked_at" in result
    assert result["reputation"] in ("clean", "suspicious", "malicious", "unknown")


def test_abuseipdb_offline_bad_ip():
    from backend.enrichment.abuseipdb import lookup

    result = lookup("185.220.101.50", "ip")
    assert result["reputation"] in ("suspicious", "unknown")


def test_mitre_lookup():
    from backend.enrichment.mitre import search_techniques

    result = search_techniques("powershell lateral movement")
    assert len(result) > 0
    assert "technique_id" in result[0]


def test_mitre_lookup_log4j():
    from backend.enrichment.mitre import search_techniques

    result = search_techniques("log4j exploit CVE-2021-44228")
    ids = [r["technique_id"] for r in result]
    assert "T1190" in ids
