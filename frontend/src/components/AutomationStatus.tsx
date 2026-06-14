import { Activity, Play, RefreshCw, Send, Square } from "lucide-react";
import type { IngestionStatus } from "../types";

type AutomationStatusProps = {
  status: IngestionStatus | null;
  loading: boolean;
  busy?: boolean;
  onStart: () => void;
  onStop: () => void;
  onOnce: () => void;
  onRefresh: () => void;
};

const formatSeconds = (seconds?: number) => {
  if (typeof seconds !== "number") return "Unknown";
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.round(seconds / 60);
  return `${minutes}m`;
};

const statusPill = (enabled: boolean) =>
  enabled
    ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
    : "bg-slate-100 text-slate-500 ring-slate-200";

export function AutomationStatus({
  status,
  loading,
  busy = false,
  onStart,
  onStop,
  onOnce,
  onRefresh,
}: AutomationStatusProps) {
  const running = Boolean(status?.running);

  return (
    <section className="mb-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Activity size={16} className="text-sky-600" />
            <h2 className="text-sm font-semibold text-slate-950">
              Mock ingestion
            </h2>
          </div>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            {loading
              ? "Checking backend status..."
              : "Feeds sample security events into the live queue."}
          </p>
        </div>
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${statusPill(
            running,
          )}`}
        >
          {running ? "On" : "Off"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-md bg-slate-50 p-3">
          <div className="font-semibold text-slate-800">
            {status?.produced_count ?? 0}
          </div>
          <div className="mt-1 text-slate-500">Produced</div>
        </div>
        <div className="rounded-md bg-slate-50 p-3">
          <div className="font-semibold text-slate-800">
            {formatSeconds(status?.interval_seconds)}
          </div>
          <div className="mt-1 text-slate-500">Interval</div>
        </div>
      </div>

      <div className="mt-3 rounded-md border border-slate-100 bg-slate-50 p-3">
        <div className="truncate font-mono text-xs text-slate-700">
          {status?.last_filename ?? "No mock event sent yet"}
        </div>
        {status?.last_ingested_at ? (
          <div className="mt-2 text-xs text-slate-500">
            Last sent: {new Date(status.last_ingested_at).toLocaleTimeString()}
          </div>
        ) : null}
        {status?.last_error ? (
          <div className="mt-2 rounded bg-red-50 px-2 py-1 text-xs text-red-700">
            {status.last_error}
          </div>
        ) : null}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <button
          type="button"
          className="inline-flex items-center justify-center gap-2 rounded-md bg-slate-950 px-3 py-2 text-xs font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          onClick={onStart}
          disabled={running || busy}
        >
          <Play size={14} />
          Start
        </button>
        <button
          type="button"
          className="inline-flex items-center justify-center gap-2 rounded-md bg-white px-3 py-2 text-xs font-semibold text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
          onClick={onStop}
          disabled={!running || busy}
        >
          <Square size={14} />
          Stop
        </button>
        <button
          type="button"
          className="inline-flex items-center justify-center gap-2 rounded-md bg-white px-3 py-2 text-xs font-semibold text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
          onClick={onOnce}
          disabled={busy}
        >
          <Send size={14} />
          One event
        </button>
        <button
          type="button"
          className="inline-flex items-center justify-center gap-2 rounded-md bg-white px-3 py-2 text-xs font-semibold text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
          onClick={onRefresh}
          disabled={busy}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>
    </section>
  );
}
