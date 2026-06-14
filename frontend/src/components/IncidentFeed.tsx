import { formatDistanceToNow } from "date-fns";
import { type ReactNode, useMemo } from "react";
import type { IncidentReport, IncidentStatus } from "../types";
import { SeverityBadge } from "./SeverityBadge";

type IncidentFeedProps = {
  incidents: IncidentReport[];
  onSelect: (id: string) => void;
  selectedId: string | null;
};

type StatusMeta = {
  label: string;
  indicator: ReactNode;
};

const statusPriority = (incident: IncidentReport) =>
  incident.status === "awaiting_approval" ? 0 : 1;

const statusMeta: Record<IncidentStatus, StatusMeta> = {
  pending: {
    label: "Pending",
    indicator: <span className="h-2 w-2 rounded-full bg-slate-400" />,
  },
  analyzing: {
    label: "Analysing",
    indicator: <span className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />,
  },
  awaiting_approval: {
    label: "Needs review",
    indicator: <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />,
  },
  approved: {
    label: "Approved",
    indicator: (
      <svg
        className="h-4 w-4 text-green-600"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M20 6 9 17l-5-5" />
      </svg>
    ),
  },
  rejected: {
    label: "Rejected",
    indicator: (
      <svg
        className="h-4 w-4 text-red-600"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M18 6 6 18" />
        <path d="m6 6 12 12" />
      </svg>
    ),
  },
  closed: {
    label: "Closed",
    indicator: <span className="text-base leading-none text-slate-500">-</span>,
  },
};

const relativeTime = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown time";

  return `${formatDistanceToNow(date)} ago`;
};

export function IncidentFeed({
  incidents,
  onSelect,
  selectedId,
}: IncidentFeedProps) {
  const sortedIncidents = useMemo(
    () =>
      [...incidents].sort((a, b) => {
        const priority = statusPriority(a) - statusPriority(b);
        if (priority !== 0) return priority;

        return (
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      }),
    [incidents],
  );

  if (incidents.length === 0) {
    return (
      <div className="flex min-h-72 flex-col items-center justify-center rounded-md border border-slate-200 bg-slate-50 px-6 text-center text-slate-500">
        <svg
          className="mb-3 h-10 w-10 text-slate-400"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
          <path d="M14 2v4a2 2 0 0 0 2 2h4" />
          <path d="M10 13H8" />
          <path d="M16 17H8" />
          <path d="M16 13h-2" />
        </svg>
        <p className="whitespace-pre-line text-sm">
          {"No incidents yet.\nPaste a log or upload a file to get started."}
        </p>
      </div>
    );
  }

  return (
    <div className="max-h-[calc(100vh-180px)] overflow-y-auto pr-1">
      <div className="space-y-2">
        {sortedIncidents.map((incident) => {
          const selected = incident.id === selectedId;
          const status = statusMeta[incident.status];

          return (
            <button
              key={incident.id}
              type="button"
              className={`w-full border-l-[3px] px-4 py-3 text-left transition ${
                selected
                  ? "border-l-blue-500 bg-blue-50"
                  : "border-l-transparent bg-white hover:bg-slate-50"
              } rounded-md border border-slate-200`}
              onClick={() => onSelect(incident.id)}
            >
              <div className="flex items-start gap-3">
                <div className="shrink-0 pt-0.5">
                  <SeverityBadge severity={incident.severity} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-3">
                    <p className="truncate text-sm font-semibold text-slate-950">
                      {incident.status === "analyzing"
                        ? "Analysing..."
                        : incident.title}
                    </p>
                    <span className="shrink-0 text-xs text-slate-500">
                      {relativeTime(incident.created_at)}
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                      {incident.incident_type}
                    </span>
                    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600">
                      {status.indicator}
                      {status.label}
                    </span>
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
