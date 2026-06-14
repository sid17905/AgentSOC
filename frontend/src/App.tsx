import { format } from "date-fns";
import { Shield } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "./api/client";
import { ApprovalPanel } from "./components/ApprovalPanel";
import { IncidentDetail } from "./components/IncidentDetail";
import { IncidentFeed } from "./components/IncidentFeed";
import { UploadPanel } from "./components/UploadPanel";
import { useIncidentStream } from "./hooks/useIncidentStream";

function App() {
  const { incidents, connected } = useIncidentStream();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [clock, setClock] = useState(() => format(new Date(), "HH:mm:ss"));
  const selectedIncident =
    incidents.find((incident) => incident.id === selectedId) ?? null;

  useEffect(() => {
    const timer = window.setInterval(() => {
      setClock(format(new Date(), "HH:mm:ss"));
    }, 1000);

    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (selectedId !== null) return;

    const urgent = incidents.find(
      (incident) => incident.status === "awaiting_approval",
    );
    if (!urgent) return;

    const timer = window.setTimeout(() => {
      setSelectedId((current) => current ?? urgent.id);
    }, 0);

    return () => window.clearTimeout(timer);
  }, [incidents, selectedId]);

  const handleApprove = async () => {
    if (!selectedId) return;
    await api.approve(selectedId);
  };

  const handleReject = async () => {
    if (!selectedId) return;
    await api.reject(selectedId);
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-950">
      <header className="flex flex-col gap-3 bg-[#0f172a] px-4 py-4 text-white sm:flex-row sm:items-center sm:justify-between lg:px-6">
        <h1 className="text-xl font-bold">AgentSOC</h1>

        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded-md bg-white/10 px-3 py-1 font-mono text-sm text-slate-200">
            {clock}
          </span>
          <span
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${
              connected
                ? "bg-green-500/10 text-green-300"
                : "bg-red-500/10 text-red-300"
            }`}
            aria-live="polite"
          >
            <span
              className={`h-2 w-2 rounded-full ${
                connected ? "bg-green-400" : "animate-pulse bg-red-400"
              }`}
            />
            {connected ? "Live" : "Reconnecting..."}
          </span>
        </div>
      </header>

      <main className="flex flex-col lg:flex-row">
        <aside className="w-full border-b border-slate-200 bg-slate-50 p-4 lg:w-[280px] lg:shrink-0 lg:border-b-0 lg:border-r">
          <UploadPanel />
        </aside>

        <section className="min-w-0 flex-1 border-b border-slate-200 bg-white p-4 lg:border-b-0 lg:border-r">
          <IncidentFeed
            incidents={incidents}
            onSelect={setSelectedId}
            selectedId={selectedId}
          />
        </section>

        <section className="w-full bg-slate-50 p-4 lg:w-[420px] lg:shrink-0">
          {selectedIncident ? (
            <>
              <ApprovalPanel
                incident={selectedIncident}
                onApprove={handleApprove}
                onReject={handleReject}
              />
              <IncidentDetail incident={selectedIncident} />
            </>
          ) : (
            <div className="flex min-h-96 flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white px-6 text-center text-slate-500">
              <Shield size={48} className="mb-4 text-slate-400" />
              <p className="text-base font-semibold text-slate-700">
                Select an incident to view details
              </p>
              <p className="mt-2 text-sm text-slate-500">
                Incidents requiring review will be highlighted
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
