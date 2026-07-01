import asyncio
from time import perf_counter

from app.agents.base import BaseAgent, EventEmitter
from app.core.config import get_settings
from app.models.domain import AgentMemory, AgentName, AgentStatus, ResearchResult, Subtask
from app.services.tavily import TavilyClient


class ResearchAgent(BaseAgent):
    name = AgentName.research

    def __init__(self, tavily: TavilyClient | None = None) -> None:
        settings = get_settings()
        self.tavily = tavily or TavilyClient(settings.tavily_api_key)

    async def run(self, memory: AgentMemory, emit_event: EventEmitter) -> AgentMemory:
        started = perf_counter()
        await self.emit(
            memory,
            emit_event,
            AgentStatus.running,
            f"Searching {len(memory.subtasks)} subtasks in parallel",
            started,
        )
        results = await asyncio.gather(
            *(self._research_subtask(memory, subtask, emit_event, started) for subtask in memory.subtasks),
            return_exceptions=True,
        )
        research_results: list[ResearchResult] = []
        next_source_id = 1
        for subtask, result in zip(memory.subtasks, results, strict=False):
            if isinstance(result, Exception):
                memory.errors.append(f"Research failed for {subtask.title}: {result}")
                research_results.append(
                    ResearchResult(subtask_id=subtask.id, subtask_title=subtask.title, sources=[], error=str(result))
                )
            else:
                for source in result.sources:
                    source.id = next_source_id
                    next_source_id += 1
                research_results.append(result)
        memory.research_results = research_results
        status = AgentStatus.partial if any(result.error for result in research_results) else AgentStatus.completed
        await self.emit(
            memory,
            emit_event,
            status,
            f"Collected {sum(len(r.sources) for r in research_results)} sources",
            started,
            {"results": [r.model_dump() for r in research_results]},
        )
        return memory

    async def _research_subtask(
        self,
        memory: AgentMemory,
        subtask: Subtask,
        emit_event: EventEmitter,
        started: float,
    ) -> ResearchResult:
        sources = await self.tavily.search(subtask.query, max_results=5)
        await self.emit(
            memory,
            emit_event,
            AgentStatus.running,
            f"{subtask.title}: {len(sources)} sources found",
            started,
            {"subtask_id": subtask.id, "source_domains": [source.domain for source in sources]},
        )
        return ResearchResult(subtask_id=subtask.id, subtask_title=subtask.title, sources=sources)
