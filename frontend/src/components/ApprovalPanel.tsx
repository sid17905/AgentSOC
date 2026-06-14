import { useState } from "react";
import type { IncidentReport } from "../types";
import { SeverityBadge } from "./SeverityBadge";

type ApprovalPanelProps = {
  incident: IncidentReport;
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
};

type Action = "approve" | "reject";

const summaryPreview = (summary: string) =>
  summary.length > 200 ? `${summary.slice(0, 200)}...` : summary;

export function ApprovalPanel({
  incident,
  onApprove,
  onReject,
}: ApprovalPanelProps) {
  const [loading, setLoading] = useState(false);
  const [activeAction, setActiveAction] = useState<Action | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [unmounted, setUnmounted] = useState(false);

  if (incident.status !== "awaiting_approval" || unmounted) {
    return null;
  }

  const confidencePercent = Math.round(
    Math.min(Math.max(incident.confidence, 0), 1) * 100,
  );

  const runAction = async (action: Action) => {
    if (loading) return;

    setLoading(true);
    setActiveAction(action);

    try {
      if (action === "approve") {
        await onApprove();
      } else {
        await onReject();
      }
      setDismissed(true);
    } catch (error) {
      console.error(`[ApprovalPanel] Failed to ${action} incident`, error);
      setLoading(false);
      setActiveAction(null);
    }
  };

  return (
    <section
      className={`sticky top-0 z-20 mb-4 overflow-hidden rounded-lg border border-amber-200 bg-amber-50 shadow-sm transition-all duration-[400ms] ${
        dismissed
          ? "max-h-0 opacity-0"
          : "max-h-[520px] opacity-100"
      }`}
      style={{ borderLeft: "4px solid #f59e0b" }}
      onTransitionEnd={() => {
        if (dismissed) setUnmounted(true);
      }}
    >
      <div className="p-4 sm:p-5">
        <div className="flex items-start gap-3">
          <span className="text-xl leading-none" aria-hidden="true">
            !
          </span>
          <div className="min-w-0 flex-1">
            <h3 className="text-base font-semibold text-slate-950">
              Agent analysis complete - awaiting your decision.
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              {summaryPreview(incident.summary)}
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3 rounded-md bg-white/70 px-3 py-2">
          <SeverityBadge severity={incident.severity} />
          <span className="text-sm font-semibold text-slate-800">
            {confidencePercent}% confidence
          </span>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <button
            type="button"
            className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-green-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-green-400"
            disabled={loading}
            onClick={() => void runAction("approve")}
          >
            {loading && activeAction === "approve" ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
            ) : null}
            Approve & Execute Playbook
          </button>

          <button
            type="button"
            className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-red-600 bg-white px-4 py-2.5 text-sm font-semibold text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:border-red-300 disabled:text-red-300"
            disabled={loading}
            onClick={() => void runAction("reject")}
          >
            {loading && activeAction === "reject" ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-red-200 border-t-red-600" />
            ) : null}
            Reject & Re-analyze
          </button>
        </div>

        <p className="mt-3 text-xs leading-5 text-slate-500">
          Approving will send a Slack notification and open a GitHub Issue for
          tracking. Rejecting will return the incident to analysis.
        </p>
      </div>
    </section>
  );
}
