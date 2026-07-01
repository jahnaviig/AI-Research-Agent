from time import perf_counter

from app.agents.base import BaseAgent, EventEmitter
from app.core.config import get_settings
from app.models.domain import AgentMemory, AgentName, AgentStatus
from app.services.llm import PlannerLLM, as_planner_json


class PlannerAgent(BaseAgent):
    name = AgentName.planner

    def __init__(self, llm: PlannerLLM | None = None) -> None:
        self.llm = llm or PlannerLLM()
        self.settings = get_settings()

    async def run(self, memory: AgentMemory, emit_event: EventEmitter) -> AgentMemory:
        started = perf_counter()
        await self.emit(memory, emit_event, AgentStatus.running, "Decomposing question", started)
        subtasks = await self.llm.plan(memory.question, self.settings.max_subtasks)
        memory.subtasks = subtasks
        await self.emit(
            memory,
            emit_event,
            AgentStatus.completed,
            f"Created {len(subtasks)} subtasks",
            started,
            {"planner_json": as_planner_json(subtasks), "subtasks": [s.model_dump() for s in subtasks]},
        )
        return memory

