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
