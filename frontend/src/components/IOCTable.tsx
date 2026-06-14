import type { IOC } from "../types";

type ReputationMeta = {
  className: string;
  label: string;
  showWarning?: boolean;
};

const getReputationMeta = (reputation?: string): ReputationMeta => {
  switch (reputation) {
    case "malicious":
      return {
        className: "text-red-600",
        label: "malicious",
        showWarning: true,
      };
    case "suspicious":
      return {
        className: "text-orange-600",
        label: "suspicious",
      };
    case "clean":
      return {
        className: "text-green-600",
        label: "clean",
      };
    default:
      return {
        className: "text-slate-500",
        label: "Pending",
      };
  }
};

const formatConfidence = (confidence: number) => {
  const normalized = Math.min(Math.max(confidence, 0), 1);

  return {
    label: `${Math.round(normalized * 100)}%`,
    width: `${normalized * 100}%`,
  };
};

type IOCTableProps = {
  iocs: IOC[];
};

export function IOCTable({ iocs }: IOCTableProps) {
  if (iocs.length === 0) {
    return (
      <div className="flex min-h-28 items-center justify-center rounded border border-slate-200 bg-slate-50 px-4 text-center text-sm text-slate-500">
        No IOCs extracted yet.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
        <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th scope="col" className="px-4 py-3">
              Type
            </th>
            <th scope="col" className="px-4 py-3">
              Value
            </th>
            <th scope="col" className="px-4 py-3">
              Confidence
            </th>
            <th scope="col" className="px-4 py-3">
              Reputation
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white text-slate-700">
          {iocs.map((ioc) => {
            const confidence = formatConfidence(ioc.confidence);
            const reputation = getReputationMeta(ioc.reputation);

            return (
              <tr key={`${ioc.type}-${ioc.value}`}>
                <td className="whitespace-nowrap px-4 py-3 font-medium text-slate-900">
                  {ioc.type}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-slate-800">
                  {ioc.value}
                </td>
                <td className="px-4 py-3">
                  <div className="flex min-w-32 items-center gap-3">
                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-sky-500"
                        style={{ width: confidence.width }}
                      />
                    </div>
                    <span className="w-10 text-right text-xs font-medium text-slate-600">
                      {confidence.label}
                    </span>
                  </div>
                </td>
                <td className={`px-4 py-3 font-medium ${reputation.className}`}>
                  <span className="inline-flex items-center gap-1.5">
                    {reputation.showWarning ? (
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
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
                        <path d="M12 9v4" />
                        <path d="M12 17h.01" />
                      </svg>
                    ) : null}
                    {reputation.label}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
