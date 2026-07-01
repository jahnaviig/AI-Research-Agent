from abc import ABC, abstractmethod
from time import perf_counter
from typing import Awaitable, Callable

from app.models.domain import AgentEvent, AgentMemory, AgentName, AgentStatus

EventEmitter = Callable[[AgentEvent], Awaitable[None]]


class BaseAgent(ABC):
    name: AgentName

    async def emit(
        self,
        memory: AgentMemory,
        emit_event: EventEmitter,
        status: AgentStatus,
        message: str,
        started_at: float,
        payload: dict | None = None,
    ) -> None:
        await emit_event(
            AgentEvent(
                session_id=memory.session_id,
                agent=self.name,
                status=status,
                message=message,
                elapsed_ms=int((perf_counter() - started_at) * 1000),
                payload=payload or {},
            )
        )

    @abstractmethod
    async def run(self, memory: AgentMemory, emit_event: EventEmitter) -> AgentMemory:
        raise NotImplementedError

