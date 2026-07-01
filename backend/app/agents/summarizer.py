import re
from time import perf_counter

from app.agents.base import BaseAgent, EventEmitter
from app.models.domain import AgentMemory, AgentName, AgentStatus, EvidenceSummary


class SummarizerAgent(BaseAgent):
    name = AgentName.summarizer

    async def run(self, memory: AgentMemory, emit_event: EventEmitter) -> AgentMemory:
        started = perf_counter()
        await self.emit(memory, emit_event, AgentStatus.running, "Summarizing evidence", started)
        summaries: list[EvidenceSummary] = []
        for result in memory.research_results:
            source_ids = [source.id for source in result.sources]
            evidence = " ".join(source.content for source in result.sources if source.content)
            summary = self._build_summary(result.subtask_title, evidence, source_ids)
            gaps = []
            if len(result.sources) < 3:
                gaps.append("Fewer than three independent sources were found.")
            if not any(source.publish_date for source in result.sources):
                gaps.append("Publish dates are missing for all sources.")
            summaries.append(
                EvidenceSummary(
                    subtask_id=result.subtask_id,
                    title=result.subtask_title,
                    summary=summary,
                    source_ids=source_ids,
                    data_gaps=gaps,
                )
            )
        memory.summaries = summaries
        await self.emit(
            memory,
            emit_event,
            AgentStatus.completed,
            f"Created {len(summaries)} evidence summaries",
            started,
            {"summaries": [summary.model_dump() for summary in summaries]},
        )
        return memory

    def _build_summary(self, title: str, evidence: str, source_ids: list[int]) -> str:
        words = re.findall(r"\w+[\w'-]*", evidence)
        trimmed = " ".join(words[:200])
        citations = " ".join(f"[Source {source_id}]" for source_id in source_ids[:3])
        if not trimmed:
            trimmed = f"No strong source text was available for {title}."
        return f"{trimmed} {citations}".strip()
