import { format } from "date-fns";
import { useState } from "react";
import type { IncidentReport, Severity } from "../types";
import { AgentThoughts } from "./AgentThoughts";
import { IOCTable } from "./IOCTable";
import { SeverityBadge } from "./SeverityBadge";

type IncidentDetailProps = {
  incident: IncidentReport;
};

type TabId = "summary" | "agent-log" | "iocs" | "mitre" | "playbook" | "report";

type Tab = {
  id: TabId;
  label: string;
  count?: number;
};

const confidenceColors: Record<Severity, string> = {
  P1: "bg-red-500",
  P2: "bg-orange-500",
  P3: "bg-yellow-500",
  P4: "bg-green-500",
};

const formatUpdatedAt = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";

  return format(date, "HH:mm dd MMM");
};

const mitreUrl = (techniqueId: string) =>
  `https://attack.mitre.org/techniques/${techniqueId.replace(".", "/")}/`;

export function IncidentDetail({ incident }: IncidentDetailProps) {
  const [activeTab, setActiveTab] = useState<TabId>("summary");
  const confidence = Math.min(Math.max(incident.confidence, 0), 1);
  const confidencePercent = Math.round(confidence * 100);

  const tabs: Tab[] = [
    { id: "summary", label: "Summary" },
    { id: "agent-log", label: "Agent Log" },
    { id: "iocs", label: "IOCs", count: incident.iocs.length },
    {
      id: "mitre",
      label: "MITRE",
      count: incident.mitre_techniques.length,
    },
    { id: "playbook", label: "Playbook" },
    { id: "report", label: "Report" },
  ];

  const downloadReport = () => {
    if (!incident.report_markdown) return;

    const blob = new Blob([incident.report_markdown], {
      type: "text/markdown",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `incident-${incident.id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-5 pt-4">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`inline-flex items-center gap-2 border-b-2 px-3 py-3 text-sm font-semibold transition ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-700"
                  : "border-transparent text-slate-500 hover:text-slate-950"
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
              {typeof tab.count === "number" ? (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">
                  {tab.count}
                </span>
              ) : null}
            </button>
          ))}
        </div>
      </div>

      <div className="p-5">
        {activeTab === "summary" ? (
          <div className="space-y-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-950">
                  {incident.title}
                </h2>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <SeverityBadge severity={incident.severity} />
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                    {incident.incident_type}
                  </span>
                </div>
              </div>
              <p className="text-sm text-slate-500">
                Last updated: {formatUpdatedAt(incident.updated_at)}
              </p>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="font-medium text-slate-700">Confidence</span>
                <span className="font-semibold text-slate-900">
                  {confidencePercent}% confidence
                </span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full rounded-full ${confidenceColors[incident.severity]}`}
                  style={{ width: `${confidencePercent}%` }}
                />
              </div>
            </div>

            <p className="text-sm leading-6 text-slate-700">{incident.summary}</p>
          </div>
        ) : null}

        {activeTab === "agent-log" ? (
          <AgentThoughts
            thoughts={incident.agent_thoughts}
            status={incident.status}
          />
        ) : null}

        {activeTab === "iocs" ? <IOCTable iocs={incident.iocs} /> : null}

        {activeTab === "mitre" ? (
          incident.mitre_techniques.length > 0 ? (
            <div className="space-y-3">
              <h3 className="text-base font-semibold text-slate-950">
                MITRE ATT&CK
              </h3>
              {incident.mitre_techniques.map((technique) => (
                <div
                  key={`${technique.technique_id}-${technique.tactic}`}
                  className="flex flex-wrap items-center gap-3 rounded-md border border-slate-200 px-4 py-3"
                >
                  <span className="rounded bg-slate-950 px-2 py-1 text-xs font-bold text-white">
                    {technique.technique_id}
                  </span>
                  <span className="text-sm font-medium text-slate-900">
                    {technique.technique_name}
                  </span>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                    {technique.tactic}
                  </span>
                  <a
                    className="ml-auto inline-flex items-center text-slate-500 transition hover:text-blue-700"
                    href={mitreUrl(technique.technique_id)}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Open ${technique.technique_id} in MITRE ATT&CK`}
                  >
                    <svg
                      className="h-4 w-4"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M15 3h6v6" />
                      <path d="M10 14 21 3" />
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    </svg>
                  </a>
                </div>
              ))}
            </div>
          ) : (
            <p className="rounded-md bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
              No MITRE techniques mapped yet.
            </p>
          )
        ) : null}

        {activeTab === "playbook" ? (
          incident.playbook_steps.length > 0 ? (
            <ol className="space-y-3">
              {incident.playbook_steps.map((step, index) => {
                const checked = incident.status === "approved";

                return (
                  <li
                    key={`${index}-${step}`}
                    className="flex items-start gap-3 rounded-md border border-slate-200 px-4 py-3"
                  >
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                      {index + 1}
                    </span>
                    <span
                      className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border ${
                        checked
                          ? "border-green-600 bg-green-600 text-white"
                          : "border-slate-300 bg-white"
                      }`}
                      aria-hidden="true"
                    >
                      {checked ? (
                        <svg
                          className="h-3.5 w-3.5"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <path d="M20 6 9 17l-5-5" />
                        </svg>
                      ) : null}
                    </span>
                    <span className="text-sm leading-6 text-slate-700">
                      {step}
                    </span>
                  </li>
                );
              })}
            </ol>
          ) : (
            <p className="rounded-md bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
              No playbook generated yet.
            </p>
          )
        ) : null}

        {activeTab === "report" ? (
          incident.report_markdown ? (
            <div className="space-y-3">
              <button
                type="button"
                className="inline-flex items-center gap-2 rounded-md bg-slate-950 px-3 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                onClick={downloadReport}
              >
                Download Report (.md)
              </button>
              <pre className="max-h-96 overflow-auto rounded-md bg-slate-950 p-4 font-mono text-sm leading-6 text-slate-100">
                {incident.report_markdown}
              </pre>
            </div>
          ) : (
            <p className="rounded-md bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
              Report will appear here once analysis is complete.
            </p>
          )
        ) : null}
      </div>
    </div>
  );
}
