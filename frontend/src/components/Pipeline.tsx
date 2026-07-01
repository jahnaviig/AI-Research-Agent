import { CheckCircle2, Clock3, Loader2, TriangleAlert } from "lucide-react";
import type { AgentEvent, AgentName, AgentStatus } from "../types/research";

const agents: AgentName[] = [
  "Planner Agent",
  "Research Agent",
  "Summarizer Agent",
  "Critic Agent",
  "Report Agent",
];

function statusIcon(status: AgentStatus) {
  if (status === "completed") return <CheckCircle2 size={18} />;
  if (status === "failed" || status === "partial") return <TriangleAlert size={18} />;
  if (status === "running") return <Loader2 className="spin" size={18} />;
  return <Clock3 size={18} />;
}

export function Pipeline({ events }: { events: AgentEvent[] }) {
  const latest = new Map<AgentName, AgentEvent>();
  events.forEach((event) => latest.set(event.agent, event));

  return (
    <section className="pipeline" aria-label="Agent pipeline progress">
      {agents.map((agent, index) => {
        const event = latest.get(agent);
        const status = event?.status ?? "pending";
        return (
          <div className={`agent-node ${status}`} key={agent}>
            <div className="node-header">
              <span className="node-icon">{statusIcon(status)}</span>
              <span className="node-index">{index + 1}</span>
            </div>
            <strong>{agent.replace(" Agent", "")}</strong>
            <span>{event?.message ?? "Waiting"}</span>
            <small>{event ? `${event.elapsed_ms} ms` : "0 ms"}</small>
          </div>
        );
      })}
    </section>
  );
}

