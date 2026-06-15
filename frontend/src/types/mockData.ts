import type { IncidentReport } from "./index";

export const MOCK_INCIDENTS: IncidentReport[] = [
  // ── P1 Critical · Ransomware ─────────────────────────────────────────────
  {
    id: "mock-boot-001",
    status: "awaiting_approval",
    incident_type: "ransomware",
    severity: "P1",
    confidence: 0.94,
    title: "Possible Ransomware Detected – finance-ws-07",
    summary:
      "EDR sensor detected powershell.exe spawning encryptor.exe on finance-ws-07. " +
      "184 files renamed with .locked extension. Outbound C2 connection to known malicious IP " +
      "185.220.101.5:443. Ransomware behaviour score 94/100. User j.singh account may be compromised.",
    iocs: [
      {
        type: "ip",
        value: "185.220.101.5",
        confidence: 0.97,
        reputation: "malicious",
      },
      {
        type: "process",
        value: "encryptor.exe",
        confidence: 0.95,
        reputation: "malicious",
      },
      {
        type: "file_extension",
        value: ".locked",
        confidence: 0.91,
        reputation: "suspicious",
      },
      {
        type: "username",
        value: "j.singh",
        confidence: 0.78,
        reputation: "suspicious",
      },
    ],
    mitre_techniques: [
      {
        technique_id: "T1486",
        technique_name: "Data Encrypted for Impact",
        tactic: "impact",
      },
      {
        technique_id: "T1059.001",
        technique_name: "PowerShell",
        tactic: "execution",
      },
      {
        technique_id: "T1071.001",
        technique_name: "Web Protocols C2",
        tactic: "command-and-control",
      },
    ],
    playbook_steps: [
      "Immediately isolate finance-ws-07 from the network",
      "Preserve full memory dump before any remediation",
      "Block C2 IP 185.220.101.5 at perimeter firewall and EDR",
      "Disable user account j.singh pending investigation",
      "Snapshot affected file shares for forensic analysis",
      "Notify incident response lead and legal/compliance team",
      "Initiate backup restoration process for .locked files",
    ],
    raw_input:
      "Jun 14 11:42:03 edr-02 sensor[9912]: process powershell.exe spawned suspicious child encryptor.exe on host finance-ws-07\n" +
      "Jun 14 11:42:06 edr-02 sensor[9912]: high file rename volume detected path=C:\\Users\\finance\\Documents extension=.locked count=184\n" +
      "Jun 14 11:42:11 edr-02 sensor[9912]: outbound connection to 185.220.101.5:443 reputation=malicious process=encryptor.exe\n" +
      "Jun 14 11:42:20 edr-02 sensor[9912]: ransomware behavior score=94 host=finance-ws-07 user=j.singh",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    agent_thoughts: [
      "[Parser] EDR log parsed successfully — 4 events",
      "[Classifier] RANSOMWARE P1 — confidence 94%",
      "[Enrichment] IP 185.220.101.5 → AbuseIPDB score 100, TOR exit node",
      "[Enrichment] Process encryptor.exe → VirusTotal 58/72 detections",
      "[MITRE] Mapped T1486 Data Encrypted for Impact (impact)",
      "[MITRE] Mapped T1059.001 PowerShell (execution)",
      "[MITRE] Mapped T1071.001 Web Protocols C2 (command-and-control)",
      "[Playbook] 7-step containment playbook generated",
      "[Status] Awaiting analyst approval",
    ],
  },

  // ── P3 Medium · Brute Force ──────────────────────────────────────────────
  {
    id: "mock-boot-002",
    status: "awaiting_approval",
    incident_type: "brute_force",
    severity: "P3",
    confidence: 0.87,
    title: "Possible Brute Force Detected – SSH auth-01",
    summary:
      "7 failed SSH login attempts from 198.51.100.23 targeting admin, root, and svc-backup accounts " +
      "within 30 seconds. The final attempt succeeded for svc-backup. Firewall logged the source IP " +
      "as exceeding failed_count threshold but allowed the connection.",
    iocs: [
      {
        type: "ip",
        value: "198.51.100.23",
        confidence: 0.89,
        reputation: "suspicious",
      },
      {
        type: "username",
        value: "svc-backup",
        confidence: 0.82,
        reputation: "suspicious",
      },
    ],
    mitre_techniques: [
      {
        technique_id: "T1110.001",
        technique_name: "Password Guessing",
        tactic: "credential-access",
      },
      {
        technique_id: "T1078",
        technique_name: "Valid Accounts",
        tactic: "defense-evasion",
      },
    ],
    playbook_steps: [
      "Block source IP 198.51.100.23 at firewall immediately",
      "Reset svc-backup credentials and rotate SSH keys",
      "Audit all actions performed by svc-backup since successful login",
      "Enable SSH rate-limiting and fail2ban on auth-01",
      "Review other hosts for lateral movement from 10.0.4.12",
    ],
    raw_input:
      "Jun 14 11:40:01 auth-01 sshd[4021]: Failed password for admin from 198.51.100.23 port 51992 ssh2\n" +
      "Jun 14 11:40:06 auth-01 sshd[4028]: Failed password for root from 198.51.100.23 port 51998 ssh2\n" +
      "Jun 14 11:40:12 auth-01 sshd[4036]: Failed password for svc-backup from 198.51.100.23 port 52005 ssh2\n" +
      "Jun 14 11:40:18 auth-01 sshd[4041]: Accepted password for svc-backup from 198.51.100.23 port 52010 ssh2\n" +
      "Jun 14 11:40:31 fw-edge-01 firewall[8831]: ALERT brute_force src=198.51.100.23 dst=10.0.4.12 service=ssh failed_count=7 action=allowed",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    agent_thoughts: [
      "[Parser] Auth + firewall log parsed — 5 events",
      "[Classifier] BRUTE_FORCE P3 — confidence 87%",
      "[Enrichment] IP 198.51.100.23 → known scanner, AbuseIPDB score 72",
      "[MITRE] Mapped T1110.001 Password Guessing (credential-access)",
      "[MITRE] Mapped T1078 Valid Accounts (defense-evasion)",
      "[Playbook] 5-step response playbook generated",
      "[Status] Awaiting analyst approval",
    ],
  },

  // ── P2 High · Phishing ───────────────────────────────────────────────────
  {
    id: "mock-boot-003",
    status: "awaiting_approval",
    incident_type: "phishing",
    severity: "P2",
    confidence: 0.81,
    title: "Possible Phishing Detected – Payroll Email accounts@",
    summary:
      "Inbound email from payroll-support@example-login.invalid to accounts@example.com " +
      "failed all authentication checks (SPF fail, DKIM none, DMARC fail). " +
      "Message body contains urgent language and a link to a typosquat domain " +
      "example-login.invalid. Source IP 203.0.113.77 has no legitimate association with the claimed sender.",
    iocs: [
      {
        type: "ip",
        value: "203.0.113.77",
        confidence: 0.85,
        reputation: "suspicious",
      },
      {
        type: "domain",
        value: "example-login.invalid",
        confidence: 0.93,
        reputation: "malicious",
      },
      {
        type: "url",
        value: "https://example-login.invalid/payroll/verify",
        confidence: 0.91,
        reputation: "malicious",
      },
      {
        type: "email",
        value: "payroll-support@example-login.invalid",
        confidence: 0.88,
        reputation: "malicious",
      },
    ],
    mitre_techniques: [
      {
        technique_id: "T1566.001",
        technique_name: "Spearphishing Attachment",
        tactic: "initial-access",
      },
      {
        technique_id: "T1598.003",
        technique_name: "Phishing for Information via Service",
        tactic: "reconnaissance",
      },
    ],
    playbook_steps: [
      "Quarantine the phishing email from all mailboxes immediately",
      "Block domain example-login.invalid at DNS and email gateway",
      "Block IP 203.0.113.77 at perimeter firewall",
      "Notify accounts team — confirm no credentials were submitted",
      "Search mail logs for other recipients of similar campaigns",
      "Submit URL to threat intel platform for tracking",
    ],
    raw_input:
      "From: payroll-support@example-login.invalid\n" +
      "To: accounts@example.com\n" +
      "Subject: Urgent payroll verification required\n\n" +
      "Your payroll account will be suspended today. Verify your account immediately:\n" +
      "https://example-login.invalid/payroll/verify\n\n" +
      "Headers: SPF=fail DKIM=none DMARC=fail Source-IP=203.0.113.77",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    agent_thoughts: [
      "[Parser] Email (.eml) parsed — headers + body extracted",
      "[Classifier] PHISHING P2 — confidence 81%",
      "[Enrichment] Domain example-login.invalid → registered 2 days ago, phishing category",
      "[Enrichment] IP 203.0.113.77 → AbuseIPDB score 88, bulletproof hosting",
      "[Enrichment] URL → VirusTotal 14/90 malicious detections",
      "[MITRE] Mapped T1566.001 Spearphishing (initial-access)",
      "[Playbook] 6-step response playbook generated",
      "[Status] Awaiting analyst approval",
    ],
  },

  // ── P2 High · Data Exfiltration ──────────────────────────────────────────
  {
    id: "mock-boot-004",
    status: "awaiting_approval",
    incident_type: "data_exfiltration",
    severity: "P2",
    confidence: 0.76,
    title: "Possible Data Exfiltration Detected – analyst2",
    summary:
      "DLP proxy detected analyst2 uploading 734 MB to external fileshare.example.net, " +
      "with 1,294 customer record pattern matches. Subsequent firewall log shows outbound " +
      "transfer to 192.0.2.88:443. IAM alert fired for unusual access token use from an " +
      "unknown country, suggesting potential account compromise or insider threat.",
    iocs: [
      {
        type: "ip",
        value: "192.0.2.88",
        confidence: 0.83,
        reputation: "suspicious",
      },
      {
        type: "domain",
        value: "fileshare.example.net",
        confidence: 0.79,
        reputation: "suspicious",
      },
      {
        type: "username",
        value: "analyst2",
        confidence: 0.71,
        reputation: "suspicious",
      },
      {
        type: "data_pattern",
        value: "customer_records (×1294)",
        confidence: 0.88,
        reputation: "sensitive",
      },
    ],
    mitre_techniques: [
      {
        technique_id: "T1048",
        technique_name: "Exfiltration Over Alternative Protocol",
        tactic: "exfiltration",
      },
      {
        technique_id: "T1539",
        technique_name: "Steal Web Session Cookie",
        tactic: "credential-access",
      },
      {
        technique_id: "T1567",
        technique_name: "Exfiltration to Cloud Storage",
        tactic: "exfiltration",
      },
    ],
    playbook_steps: [
      "Suspend analyst2 account and revoke all active tokens immediately",
      "Block egress to 192.0.2.88 and fileshare.example.net at firewall",
      "Capture and preserve DLP logs for legal/forensic chain of custody",
      "Identify all data touched by analyst2 in last 30 days",
      "Notify Data Protection Officer — potential regulatory breach (GDPR/PCI)",
      "Coordinate with HR for insider threat investigation protocol",
      "Assess blast radius: enumerate all customer records at risk",
    ],
    raw_input:
      "Jun 14 11:45:44 proxy-01 dlp[4411]: large upload detected user=analyst2 dst=fileshare.example.net bytes=734003200\n" +
      "Jun 14 11:45:46 proxy-01 dlp[4411]: sensitive pattern match type=customer_records count=1294\n" +
      "Jun 14 11:45:49 proxy-01 firewall[9244]: outbound transfer src=10.0.8.21 dst=192.0.2.88 port=443 action=allowed\n" +
      "Jun 14 11:46:01 iam-01 auth[8142]: unusual access token use user=analyst2 country=unknown",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    agent_thoughts: [
      "[Parser] DLP + firewall + IAM log parsed — 4 events",
      "[Classifier] DATA_EXFILTRATION P2 — confidence 76%",
      "[Enrichment] IP 192.0.2.88 → datacenter IP, no business justification",
      "[Enrichment] Domain fileshare.example.net → not on approved vendor list",
      "[MITRE] Mapped T1048 Exfiltration Over Alternative Protocol (exfiltration)",
      "[MITRE] Mapped T1567 Exfiltration to Cloud Storage (exfiltration)",
      "[Playbook] 7-step containment + legal playbook generated",
      "[Status] Awaiting analyst approval",
    ],
  },
];

// Set USE_MOCK = true to bypass the backend during development.
// When false, incidents are loaded live from the backend via WebSocket.
export const USE_MOCK = false;