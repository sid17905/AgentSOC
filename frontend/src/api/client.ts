import axios from "axios";
import type { AgentInput, IncidentReport } from "../types";

// Uses Vite proxy (see vite.config.ts) - no hardcoded port needed
const BASE = "/api/v1";

export const api = {
  analyze: (input: AgentInput) =>
    axios.post<{ incident_id: string }>(`${BASE}/analyze`, input),

  getIncidents: () => axios.get<IncidentReport[]>(`${BASE}/incidents`),

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
