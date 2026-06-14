from datetime import datetime

from backend.reporting.report_generator import generate_report
from backend.schemas.incident import (
    IOC,
    MITRETechnique,
    IncidentReport,
    IncidentStatus,
    IncidentType,
    Severity,
)


def make_sample_incident() -> IncidentReport:
    return IncidentReport(
        id="inc-test-001",
        title="Test Ransomware Incident",
        status=IncidentStatus.AWAITING_APPROVAL,
        incident_type=IncidentType.RANSOMWARE,
        severity=Severity.P1,
        confidence=0.92,
        summary="Ransomware activity detected on endpoint web-01.",
        iocs=[
            IOC(
                type="ip",
                value="185.220.101.5",
                confidence=0.9,
                reputation="malicious",
            ),
            IOC(type="hash", value="a3f1b2c3d4e5f6a7b8c9", confidence=0.95),
        ],
        mitre_techniques=[
            MITRETechnique(
                technique_id="T1486",
                technique_name="Data Encrypted for Impact",
                tactic="impact",
            )
        ],
        playbook_steps=[
            "Isolate affected hosts immediately",
            "Preserve memory dumps before remediation",
            "Block C2 IPs at perimeter firewall",
        ],
        raw_input="Jan 15 14:22:01 web-01 kernel: [ransomware.exe] encrypting /data/",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        agent_thoughts=["[Parser] Log parsed", "[Classifier] Ransomware P1"],
    )


def test_generate_report_contains_title():
    assert "Test Ransomware Incident" in generate_report(make_sample_incident())


def test_generate_report_contains_iocs():
    report = generate_report(make_sample_incident())
    assert "185.220.101.5" in report
    assert "malicious" in report


def test_generate_report_contains_mitre():
    report = generate_report(make_sample_incident())
    assert "T1486" in report
    assert "Data Encrypted for Impact" in report


def test_generate_report_contains_playbook():
    assert "Isolate affected hosts" in generate_report(make_sample_incident())


def test_generate_report_no_iocs():
    incident = make_sample_incident()
    incident.iocs = []
    assert "No IOCs extracted" in generate_report(incident)


def test_generate_report_mentions_ollama():
    report = generate_report(make_sample_incident())
    assert "Ollama" in report
    assert "Anthropic" not in report
