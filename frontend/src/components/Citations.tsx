import { ExternalLink } from "lucide-react";
import type { ResearchResult, Source } from "../types/research";

export function Citations({ results }: { results: ResearchResult[] }) {
  const sources = results.flatMap((result) => result.sources.map((source) => ({ ...source, subtask: result.subtask_title })));
  if (sources.length === 0) return null;

  return (
    <section className="citations">
      <div className="section-title">
        <h2>Sources</h2>
        <span>{sources.length} collected</span>
      </div>
      <div className="source-grid">
        {sources.map((source: Source & { subtask: string }) => (
          <article className="source-card" key={`${source.subtask}-${source.id}-${source.url}`}>
            <div className="source-meta">
              <span>Source {source.id}</span>
              <span>{Math.round(source.domain_score * 100)} domain score</span>
            </div>
            <h3>{source.title}</h3>
            <p>{source.content.slice(0, 220)}...</p>
            <div className="source-footer">
              <span>{source.publish_date ?? "No date"}</span>
              <a href={source.url} target="_blank" rel="noreferrer">
                {source.domain}
                <ExternalLink size={14} />
              </a>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

