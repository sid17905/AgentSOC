import axios from "axios";
import type { AgentInput, IncidentReport, IngestionStatus } from "../types";

// Uses Vite proxy (see vite.config.ts) - no hardcoded port needed

const BASE = `${import.meta.env.VITE_API_URL ?? ""}/api/v1`;

export const api = {
  analyze: (input: AgentInput) =>
    axios.post<{ incident_id: string }>(`${BASE}/analyze`, input),

  getIncidents: () =>
    axios.get<IncidentReport[]>(`${BASE}/incidents`, {
      params: { _: Date.now() },
    }),

  getIncident: (id: string) => axios.get<IncidentReport>(`${BASE}/incidents/${id}`),

  approve: (id: string) =>
    axios.post<IncidentReport>(`${BASE}/incidents/${id}/approve`),

  reject: (id: string) =>
    axios.post<IncidentReport>(`${BASE}/incidents/${id}/reject`),

  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return axios.post<AgentInput>(`${BASE}/upload`, form);
  },

  getMockIngestionStatus: () =>
    axios.get<IngestionStatus>(`${BASE}/ingestion/mock/status`),

  startMockIngestion: (intervalSeconds = 30, limit = 8) =>
    axios.post<IngestionStatus>(`${BASE}/ingestion/mock/start`, null, {
      params: { interval_seconds: intervalSeconds, limit },
    }),

  stopMockIngestion: () =>
    axios.post<IngestionStatus>(`${BASE}/ingestion/mock/stop`),

  ingestMockOnce: () =>
    axios.post<{ source: string; filename: string; incident_id: string | null }>(
      `${BASE}/ingestion/mock/once`,
    ),
};

export async function fetchIncidents(): Promise<IncidentReport[]> {
  const res = await api.getIncidents();
  return res.data;
}

export async function fetchIncident(id: string): Promise<IncidentReport> {
  const res = await api.getIncident(id);
  return res.data;
}

export async function approveIncident(id: string): Promise<IncidentReport> {
  const res = await api.approve(id);
  return res.data;
}

export async function rejectIncident(id: string): Promise<IncidentReport> {
  const res = await api.reject(id);
  return res.data;
}

export function getPdfReportUrl(id: string): string {
  return `${BASE}/incidents/${id}/report/pdf`;
}
