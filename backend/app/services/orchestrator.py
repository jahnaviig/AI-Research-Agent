import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter

from app.agents.critic import CriticAgent
from app.agents.planner import PlannerAgent
from app.agents.report import ReportAgent
from app.agents.research import ResearchAgent
from app.agents.summarizer import SummarizerAgent
from app.core.config import get_settings
from app.models.domain import AgentEvent, AgentMemory, AgentName, AgentStatus
from app.services.events import event_bus
from app.services.persistence import ResearchRepository


class AgentOrchestrator:
    def __init__(self, repository: ResearchRepository | None = None) -> None:
        self.repository = repository
        self.settings = get_settings()
        self.agents = [
            PlannerAgent(),
            ResearchAgent(),
            SummarizerAgent(),
            CriticAgent(),
            ReportAgent(),
        ]

    async def run(self, memory: AgentMemory) -> AgentMemory:
        started = perf_counter()
        if self.repository:
            await self.repository.create_session(memory)
        try:
            return await asyncio.wait_for(
                self._run_sequential(memory, self._emit),
                timeout=self.settings.pipeline_timeout_seconds,
            )
        except TimeoutError:
            memory.errors.append("Pipeline timed out; returning partial result.")
            await self._emit(
                AgentEvent(
                    session_id=memory.session_id,
                    agent=AgentName.report,
                    status=AgentStatus.partial,
                    message="120s timeout reached; returning partial result",
                    elapsed_ms=int((perf_counter() - started) * 1000),
                    payload=memory.model_dump(),
                )
            )
            if self.repository:
                await self.repository.save_memory(memory, status="partial")
            return memory
        except Exception as exc:
            memory.errors.append(str(exc))
            await self._emit(
                AgentEvent(
                    session_id=memory.session_id,
                    agent=AgentName.report,
                    status=AgentStatus.failed,
                    message=f"Pipeline failed: {exc}",
                    elapsed_ms=int((perf_counter() - started) * 1000),
                )
            )
            if self.repository:
                await self.repository.save_memory(memory, status="failed")
            return memory

    async def _run_sequential(
        self,
        memory: AgentMemory,
        emit_event: Callable[[AgentEvent], Awaitable[None]],
    ) -> AgentMemory:
        for agent in self.agents:
            try:
                memory = await agent.run(memory, emit_event)
            except Exception as exc:
                memory.errors.append(f"{agent.name.value} failed: {exc}")
                await emit_event(
                    AgentEvent(
                        session_id=memory.session_id,
                        agent=agent.name,
                        status=AgentStatus.failed,
                        message=str(exc),
                        payload={"errors": memory.errors},
                    )
                )
                if agent.name in {AgentName.planner, AgentName.report}:
                    break
        if self.repository:
            await self.repository.save_memory(memory, status="partial" if memory.errors else "completed")
        return memory

    async def _emit(self, event: AgentEvent) -> None:
        await event_bus.publish(event)
        if self.repository:
            await self.repository.save_event(event)

