import { FormEvent, useMemo, useRef, useState } from "react";
import { Play, Square } from "lucide-react";
import { startResearch, sessionWebSocketUrl } from "./api/client";
import { Citations } from "./components/Citations";
import { ConfidenceReview } from "./components/ConfidenceReview";
import { Pipeline } from "./components/Pipeline";
import type { AgentEvent, ClaimAssessment, ReportArtifact, ResearchResult, Source, Summary } from "./types/research";
import "./styles/app.css";

export default function App() {
  const [question, setQuestion] = useState("What are the strongest current arguments for and against multi-agent AI research systems in production?");
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const researchResults = useMemo(() => latestPayload<ResearchResult[]>(events, "Research Agent", "results") ?? [], [events]);
  const summaries = useMemo(() => latestPayload<Summary[]>(events, "Summarizer Agent", "summaries") ?? [], [events]);
  const claims = useMemo(() => latestPayload<ClaimAssessment[]>(events, "Critic Agent", "assessments") ?? [], [events]);
  const report = useMemo(() => latestPayload<ReportArtifact>(events, "Report Agent", "markdown"), [events]);
  const sourceById = useMemo(() => {
    const map = new Map<number, Source>();
    researchResults.flatMap((result) => result.sources).forEach((source) => map.set(source.id, source));
    return map;
  }, [researchResults]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setEvents([]);
    setRunning(true);
    socketRef.current?.close();
    try {
      const response = await startResearch(question);
      const socket = new WebSocket(sessionWebSocketUrl(response.websocket_url));
      socketRef.current = socket;
      socket.onmessage = (message) => {
        const eventData = JSON.parse(message.data) as AgentEvent;
        setEvents((current) => [...current, eventData]);
        if (eventData.agent === "Report Agent" && ["completed", "failed", "partial"].includes(eventData.status)) {
          setRunning(false);
        }
      };
      socket.onerror = () => {
        setError("WebSocket connection failed.");
        setRunning(false);
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setRunning(false);
    }
  }

  function stop() {
    socketRef.current?.close();
    setRunning(false);
  }

  return (
    <main className="app-shell">
      <section className="workbench">
        <div className="brand-bar">
          <div>
            <h1>Multi-Agent Research Console</h1>
            <p>Planner, parallel Research, Summarizer, semantic Critic, and Report agents.</p>
          </div>
          <span className={running ? "live-pill on" : "live-pill"}>{running ? "Live" : "Ready"}</span>
        </div>

        <form className="question-panel" onSubmit={submit}>
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} minLength={8} />
          <div className="form-actions">
            <button type="submit" disabled={running}>
              <Play size={17} />
              Run research
            </button>
            <button type="button" className="secondary" onClick={stop} disabled={!running}>
              <Square size={16} />
              Stop stream
            </button>
          </div>
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      <Pipeline events={events} />

      <section className="evidence-band">
        <div>
          <div className="section-title">
            <h2>Evidence Summaries</h2>
            <span>{summaries.length} subtasks</span>
          </div>
          <div className="summary-list">
            {summaries.map((summary) => (
              <article className="summary-row" key={summary.subtask_id}>
                <h3>{summary.title}</h3>
                <p>{summary.summary}</p>
                <div className="citation-buttons">
                  {summary.source_ids.map((sourceId) => (
                    <button
                      type="button"
                      className="citation-chip"
                      key={`${summary.subtask_id}-${sourceId}`}
                      onClick={() => setSelectedSource(sourceById.get(sourceId) ?? null)}
                    >
                      Source {sourceId}
                    </button>
                  ))}
                </div>
                {summary.data_gaps.length > 0 && <small>Gaps: {summary.data_gaps.join(" ")}</small>}
              </article>
            ))}
          </div>
        </div>
        <div className="side-stack">
          {selectedSource && (
            <article className="source-preview">
              <span>Selected source</span>
              <h3>{selectedSource.title}</h3>
              <p>{selectedSource.content.slice(0, 340)}...</p>
              <a href={selectedSource.url} target="_blank" rel="noreferrer">
                {selectedSource.domain}
              </a>
            </article>
          )}
          <ConfidenceReview claims={claims} />
        </div>
      </section>

      <Citations results={researchResults} />

      {report?.markdown && (
        <section className="report-preview">
          <div className="section-title">
            <h2>Report Markdown</h2>
            <span>PDF export handled by backend</span>
          </div>
          <pre>{report.markdown}</pre>
        </section>
      )}
    </main>
  );
}

function latestPayload<T>(events: AgentEvent[], agent: string, key: string): T | undefined {
  const event = [...events].reverse().find((item) => item.agent === agent && item.payload && key in item.payload);
  if (!event) return undefined;
  if (key === "markdown") return event.payload as T;
  return event.payload[key] as T;
}
