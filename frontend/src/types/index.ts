export type Severity = "P1" | "P2" | "P3" | "P4";

export type IncidentType =
  | "ransomware"
  | "phishing"
  | "data_exfiltration"
  | "lateral_movement"
  | "brute_force"
  | "unknown";

export type IncidentStatus =
  | "pending"
  | "analyzing"
  | "awaiting_approval"
  | "approved"
  | "rejected"
  | "closed";

export interface IOC {
  type: string;
  value: string;
  confidence: number;
  reputation?: string;
}

export interface MITRETechnique {
  technique_id: string;
  technique_name: string;
  tactic: string;
}

export interface IncidentReport {
  id: string;
  status: IncidentStatus;
  incident_type: IncidentType;
  severity: Severity;
  confidence: number;
  title: string;
  summary: string;
  iocs: IOC[];
  mitre_techniques: MITRETechnique[];
  playbook_steps: string[];
  raw_input: string;
  created_at: string;
  updated_at: string;
  report_markdown?: string;
  agent_thoughts: string[];
}

export interface AgentInput {
  input_type: "log" | "pdf" | "image" | "email" | "json";
  content: string;
  filename?: string;
}

export interface IngestionStatus {
  running?: boolean;
  produced_count?: number;
  interval_seconds?: number;
  limit?: number | null;
  last_filename?: string | null;
  last_incident_id?: string | null;
  last_error?: string | null;
  last_ingested_at?: string | null;
  enabled?: boolean;
  directory?: string | null;
  auto_fetch_enabled?: boolean;
  auto_fetch_sources?: string[];
  auto_fetch_interval_seconds?: number;
}
