import { useEffect, useRef, useState } from "react";
import { fetchIncidents } from "../api/client";
import type { IncidentReport } from "../types";
import { MOCK_INCIDENTS, USE_MOCK } from "../types/mockData";

// Relative WS path - resolved by Vite proxy to ws://localhost:8000
const WS_PROTOCOL = window.location.protocol === "https:" ? "wss" : "ws";
const WS_URL = `${WS_PROTOCOL}://${window.location.host}/ws/incidents`;

export function useIncidentStream() {
  const [incidents, setIncidents] = useState<IncidentReport[]>(
    USE_MOCK ? MOCK_INCIDENTS : [],
  );
  const [connected, setConnected] = useState(USE_MOCK);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (USE_MOCK) return;

    let isMounted = true;

    fetchIncidents()
      .then((fetchedIncidents) => {
        if (isMounted) {
          setIncidents((current) => mergeIncidents(current, fetchedIncidents));
        }
      })
      .catch((error) => {
        console.warn("[API] Failed to fetch incidents", error);
      });

    function connect() {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMounted) return;
        setConnected(true);
        if (retryRef.current) clearTimeout(retryRef.current);
      };

      ws.onclose = () => {
        if (!isMounted) return;
        setConnected(false);
        retryRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (Array.isArray(msg)) {
            setIncidents((current) => mergeIncidents(current, msg));
          } else if (msg.type === "incident_update") {
            setIncidents((current) => mergeIncidents(current, [msg.data]));
          }
        } catch {
          console.warn("[WS] Failed to parse message", event.data);
        }
      };
    }

    connect();
    return () => {
      isMounted = false;
      if (retryRef.current) clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, []);

  return { incidents, connected };
}

function mergeIncidents(
  currentIncidents: IncidentReport[],
  incomingIncidents: IncidentReport[],
): IncidentReport[] {
  const byId = new Map<string, IncidentReport>();

  for (const incident of currentIncidents) {
    byId.set(incident.id, incident);
  }
  for (const incident of incomingIncidents) {
    byId.set(incident.id, incident);
  }

  return Array.from(byId.values()).sort(
    (left, right) =>
      new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
  );
}
