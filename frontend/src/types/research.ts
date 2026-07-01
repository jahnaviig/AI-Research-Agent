export type AgentName =
  | "Planner Agent"
  | "Research Agent"
  | "Summarizer Agent"
  | "Critic Agent"
  | "Report Agent";

export type AgentStatus = "pending" | "running" | "completed" | "failed" | "partial";

export interface AgentEvent {
  session_id: string;
  agent: AgentName;
  status: AgentStatus;
  message: string;
  elapsed_ms: number;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface Source {
  id: number;
  title: string;
  url: string;
  domain: string;
  domain_score: number;
  publish_date?: string | null;
  content: string;
}

export interface ResearchResult {
  subtask_id: string;
  subtask_title: string;
  sources: Source[];
  error?: string | null;
}

export interface Summary {
  subtask_id: string;
  title: string;
  summary: string;
  source_ids: number[];
  data_gaps: string[];
}

export interface ClaimAssessment {
  claim: string;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  score: number;
  source_ids: number[];
  rationale: string;
}

export interface ReportArtifact {
  markdown: string;
  pdf_path?: string | null;
  bibliography: string[];
}

