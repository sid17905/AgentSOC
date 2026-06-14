import type { IncidentReport } from "./index";

export const MOCK_INCIDENTS: IncidentReport[] = [
  {
    id: "mock-001",
    status: "awaiting_approval",
    incident_type: "ransomware",
    severity: "P1",
    confidence: 0.93,
    title: "Ransomware Activity Detected — web-01",
    summary:
      "Suspicious file encryption process detected on web-01. Multiple .enc files created.",
    iocs: [
      {
        type: "ip",
        value: "185.220.101.5",
        confidence: 0.92,
        reputation: "malicious",
      },
      {
        type: "hash",
        value: "a3f1b2c3d4e5f6",
        confidence: 0.88,
        reputation: "suspicious",
      },
    ],
    mitre_techniques: [
      {
        technique_id: "T1486",
        technique_name: "Data Encrypted for Impact",
        tactic: "impact",
      },
    ],
    playbook_steps: [
      "Isolate affected host immediately",
      "Preserve memory dump before remediation",
      "Block C2 IPs at perimeter firewall",
    ],
    raw_input: "Jan 15 14:22:01 web-01 kernel: [ransomware.exe] encrypting /data/",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    agent_thoughts: [
      "[Parser] Log parsed successfully",
      "[Classifier] Ransomware P1 — confidence 93%",
      "[Enrichment] IP 185.220.101.5 flagged malicious via AbuseIPDB",
      "[MITRE] Mapped to T1486 Data Encrypted for Impact",
    ],
  },
  {
    id: "mock-002",
    status: "analyzing",
    incident_type: "phishing",
    severity: "P2",
    confidence: 0.71,
    title: "Phishing Email — HR Dept",
    summary: "Email with spoofed sender and malicious link detected.",
    iocs: [],
    mitre_techniques: [],
    playbook_steps: [],
    raw_input:
      "From: hr@example-corp.com\nSubject: Payroll update\nLink: https://example-login.invalid/payroll",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    agent_thoughts: ["[Parser] Email parsed", "[Classifier] Phishing suspected…"],
  },
];

// Set USE_MOCK = true to bypass the backend during development.
export const USE_MOCK = false;
