import asyncio

from app.agents.critic import CriticAgent
from app.agents.planner import PlannerAgent
from app.agents.research import ResearchAgent
from app.agents.summarizer import SummarizerAgent
from app.models.domain import AgentEvent, AgentMemory, Source
from app.services.tavily import TavilyClient


async def collect(_: AgentEvent) -> None:
    return None


class FakeTavily(TavilyClient):
    def __init__(self) -> None:
        super().__init__(api_key=None)

    async def search(self, query: str, max_results: int = 5) -> list[Source]:
        await asyncio.sleep(0.01)
        return [
            Source(
                id=1,
                title="Primary evidence",
                url="https://example.edu/evidence",
                domain="example.edu",
                domain_score=0.95,
                publish_date="2026-02-01",
                content=f"{query} has credible evidence, measured outcomes, and clear caveats.",
            )
        ]


async def test_planner_returns_json_ready_subtasks() -> None:
    memory = AgentMemory(session_id="s1", question="How reliable are agentic research systems?")
    result = await PlannerAgent().run(memory, collect)
    assert 3 <= len(result.subtasks) <= 6
    assert all(subtask.query for subtask in result.subtasks)


async def test_research_agent_runs_subtasks_in_parallel() -> None:
    memory = await PlannerAgent().run(
        AgentMemory(session_id="s2", question="How reliable are agentic research systems?"),
        collect,
    )
    result = await ResearchAgent(FakeTavily()).run(memory, collect)
    assert len(result.research_results) == len(memory.subtasks)
    assert all(item.sources for item in result.research_results)


async def test_summarizer_adds_inline_source_citations() -> None:
    memory = await PlannerAgent().run(
        AgentMemory(session_id="s3", question="How reliable are agentic research systems?"),
        collect,
    )
    memory = await ResearchAgent(FakeTavily()).run(memory, collect)
    result = await SummarizerAgent().run(memory, collect)
    assert result.summaries
    assert "[Source 1]" in result.summaries[0].summary


async def test_critic_scores_claims() -> None:
    memory = await PlannerAgent().run(
        AgentMemory(session_id="s4", question="How reliable are agentic research systems?"),
        collect,
    )
    memory = await ResearchAgent(FakeTavily()).run(memory, collect)
    memory = await SummarizerAgent().run(memory, collect)
    result = await CriticAgent().run(memory, collect)
    assert result.critic is not None
    assert result.critic.assessments

