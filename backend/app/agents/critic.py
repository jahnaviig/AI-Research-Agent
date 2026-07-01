import re
from itertools import combinations
from time import perf_counter

import numpy as np

from app.agents.base import BaseAgent, EventEmitter
from app.models.domain import (
    AgentMemory,
    AgentName,
    AgentStatus,
    ClaimAssessment,
    Confidence,
    CriticResult,
)


class CriticAgent(BaseAgent):
    name = AgentName.critic

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None

    async def run(self, memory: AgentMemory, emit_event: EventEmitter) -> AgentMemory:
        started = perf_counter()
        await self.emit(memory, emit_event, AgentStatus.running, "Verifying claims semantically", started)
        source_texts = {
            source.id: source.content
            for result in memory.research_results
            for source in result.sources
            if source.content
        }
        assessments: list[ClaimAssessment] = []
        for summary in memory.summaries:
            for claim in self._claims(summary.summary):
                score, source_ids = self._score_claim(claim, source_texts)
                confidence = Confidence.high if score >= 0.72 else Confidence.medium if score >= 0.48 else Confidence.low
                assessments.append(
                    ClaimAssessment(
                        claim=claim,
                        confidence=confidence,
                        score=round(score, 3),
                        source_ids=source_ids,
                        rationale="Cosine similarity against raw source text.",
                    )
                )
        contradictions = self._find_contradictions([summary.summary for summary in memory.summaries])
        memory.critic = CriticResult(assessments=assessments, contradictions=contradictions)
        await self.emit(
            memory,
            emit_event,
            AgentStatus.completed,
            f"Scored {len(assessments)} claims",
            started,
            memory.critic.model_dump(),
        )
        return memory

    def _claims(self, text: str) -> list[str]:
        claims = [claim.strip() for claim in re.split(r"(?<=[.!?])\s+", text) if len(claim.split()) >= 6]
        return claims[:8]

    def _score_claim(self, claim: str, source_texts: dict[int, str]) -> tuple[float, list[int]]:
        if not source_texts:
            return 0.0, []
        try:
            model = self._load_model()
            vectors = model.encode([claim, *source_texts.values()], normalize_embeddings=True)
            scores = np.dot(vectors[1:], vectors[0])
        except Exception:
            claim_terms = set(re.findall(r"\w+", claim.lower()))
            scores = np.array(
                [
                    len(claim_terms & set(re.findall(r"\w+", text.lower()))) / max(len(claim_terms), 1)
                    for text in source_texts.values()
                ]
            )
        ordered = sorted(zip(source_texts.keys(), scores, strict=False), key=lambda item: item[1], reverse=True)
        return float(ordered[0][1]), [source_id for source_id, _score in ordered[:3]]

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _find_contradictions(self, summaries: list[str]) -> list[str]:
        contradictions: list[str] = []
        markers = [("increase", "decrease"), ("higher", "lower"), ("supports", "rejects")]
        for left, right in combinations(summaries, 2):
            left_lower = left.lower()
            right_lower = right.lower()
            for a, b in markers:
                if a in left_lower and b in right_lower:
                    contradictions.append(f"Potential contradiction: one subtask says '{a}' while another says '{b}'.")
        return contradictions
