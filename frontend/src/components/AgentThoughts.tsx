import { useEffect, useRef } from "react";
import type { IncidentStatus } from "../types";

type AgentThoughtsProps = {
  thoughts: string[];
  status: IncidentStatus;
};

const formatTimestamp = (index: number, count: number) =>
  new Date(Date.now() - (count - index) * 2000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

export function AgentThoughts({ thoughts, status }: AgentThoughtsProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thoughts]);

  return (
    <div className="max-h-72 overflow-y-auto rounded bg-slate-950 p-4 font-mono text-sm leading-6 text-slate-200 shadow-inner">
      <style>
        {`
          @keyframes agent-thinking-pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.35; }
          }
        `}
      </style>
      {thoughts.map((thought, index) => (
        <div key={`${index}-${thought}`} className="whitespace-pre-wrap">
          <span className="text-slate-500">
            [{formatTimestamp(index, thoughts.length)}]
          </span>{" "}
          <span>{thought}</span>
        </div>
      ))}
      {status === "analyzing" ? (
        <div
          className="mt-2 text-emerald-300"
          style={{ animation: "agent-thinking-pulse 1s ease-in-out infinite" }}
        >
          Agent is thinking...
        </div>
      ) : null}
      <div ref={bottomRef} />
    </div>
  );
}
