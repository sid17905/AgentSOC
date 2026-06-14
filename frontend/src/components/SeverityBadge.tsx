import type { Severity } from "../types";

type SeverityMeta = {
  background: string;
  color: string;
  label: string;
};

const severityMeta: Record<Severity, SeverityMeta> = {
  P1: {
    background: "#fee2e2",
    color: "#dc2626",
    label: "P1 Critical",
  },
  P2: {
    background: "#ffedd5",
    color: "#ea580c",
    label: "P2 High",
  },
  P3: {
    background: "#fef9c3",
    color: "#ca8a04",
    label: "P3 Medium",
  },
  P4: {
    background: "#dcfce7",
    color: "#16a34a",
    label: "P4 Low",
  },
};

type SeverityBadgeProps = {
  severity: Severity;
};

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const meta = severityMeta[severity];

  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold"
      style={{ backgroundColor: meta.background, color: meta.color }}
    >
      {meta.label}
    </span>
  );
}
