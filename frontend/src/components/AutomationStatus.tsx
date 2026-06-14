import { Activity, Clock, FolderInput, RadioTower } from "lucide-react";
import type { IngestionStatus } from "../types";

type AutomationStatusProps = {
  status: IngestionStatus | null;
  loading: boolean;
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

export function AutomationStatus({ status, loading }: AutomationStatusProps) {
  const folderEnabled = Boolean(status?.enabled);
  const fetchEnabled = Boolean(status?.auto_fetch_enabled);
  const fetchSources = status?.auto_fetch_sources ?? [];

  return (
    <section className="mb-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Activity size={16} className="text-sky-600" />
            <h2 className="text-sm font-semibold text-slate-950">
              Autonomous intake
            </h2>
          </div>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            {loading
              ? "Checking backend status..."
              : "Logs are collected by the backend on a schedule."}
          </p>
        </div>
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${statusPill(
            folderEnabled || fetchEnabled,
          )}`}
        >
          {folderEnabled || fetchEnabled ? "On" : "Off"}
        </span>
      </div>

      <div className="space-y-3">
        <div className="rounded-md border border-slate-100 bg-slate-50 p-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
            <RadioTower size={16} />
            Scheduled log fetch
          </div>
          <p className="mt-2 text-xs text-slate-500">
            {fetchEnabled
              ? `Fetches every ${formatSeconds(status?.auto_fetch_interval_seconds)}`
              : "Disabled"}
          </p>
          {fetchSources.length > 0 ? (
            <ul className="mt-2 space-y-1">
              {fetchSources.map((source) => (
                <li
                  key={source}
                  className="truncate rounded bg-white px-2 py-1 font-mono text-xs text-slate-600"
                  title={source}
                >
                  {source}
                </li>
              ))}
            </ul>
          ) : null}
        </div>

        <div className="rounded-md border border-slate-100 bg-slate-50 p-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
            <FolderInput size={16} />
            Inbox folder
          </div>
          <p className="mt-2 break-all font-mono text-xs text-slate-600">
            {status?.directory ?? "Not configured"}
          </p>
          <p className="mt-2 text-xs text-slate-500">
            {folderEnabled
              ? `Checks every ${formatSeconds(status?.interval_seconds)}`
              : "Disabled"}
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Clock size={14} />
          New fetched logs appear in the incident feed without manual upload.
        </div>
      </div>
    </section>
  );
}
