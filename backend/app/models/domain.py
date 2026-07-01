from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentName(str, Enum):
    planner = "Planner Agent"
    research = "Research Agent"
    summarizer = "Summarizer Agent"
    critic = "Critic Agent"
    report = "Report Agent"


class AgentStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    partial = "partial"


class Confidence(str, Enum):
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"


class Subtask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    query: str
    rationale: str


class Source(BaseModel):
    id: int
    title: str
    url: str
    domain: str
    domain_score: float = Field(ge=0, le=1)
    publish_date: str | None = None
    content: str


class ResearchResult(BaseModel):
    subtask_id: str
    subtask_title: str
    sources: list[Source]
    error: str | None = None


class EvidenceSummary(BaseModel):
    subtask_id: str
    title: str
    summary: str
    source_ids: list[int]
    data_gaps: list[str] = Field(default_factory=list)


class ClaimAssessment(BaseModel):
    claim: str
    confidence: Confidence
    score: float
    source_ids: list[int]
    rationale: str


class CriticResult(BaseModel):
    assessments: list[ClaimAssessment]
    contradictions: list[str] = Field(default_factory=list)


class ReportArtifact(BaseModel):
    markdown: str
    pdf_path: str | None = None
    bibliography: list[str]


class AgentEvent(BaseModel):
    session_id: str
    agent: AgentName
    status: AgentStatus
    message: str
    elapsed_ms: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentMemory(BaseModel):
    session_id: str
    question: str
    subtasks: list[Subtask] = Field(default_factory=list)
    research_results: list[ResearchResult] = Field(default_factory=list)
    summaries: list[EvidenceSummary] = Field(default_factory=list)
    critic: CriticResult | None = None
    report: ReportArtifact | None = None
    errors: list[str] = Field(default_factory=list)

