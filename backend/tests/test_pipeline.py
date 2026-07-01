from app.agents.report import ReportAgent
from app.models.domain import AgentMemory, Source
from app.services.orchestrator import AgentOrchestrator
from app.services.tavily import TavilyClient


class FakeTavily(TavilyClient):
    def __init__(self) -> None:
        super().__init__(api_key=None)

    async def search(self, query: str, max_results: int = 5) -> list[Source]:
        return [
            Source(
                id=1,
                title="Evidence source",
                url="https://example.edu/source",
                domain="example.edu",
                domain_score=0.95,
                publish_date="2026-03-01",
                content=f"{query} is supported by evidence and includes known limitations.",
            )
        ]


async def test_full_pipeline_with_mocked_external_api(tmp_path) -> None:
    orchestrator = AgentOrchestrator()
    orchestrator.agents[1].tavily = FakeTavily()
    orchestrator.agents[4] = ReportAgent(export_dir=str(tmp_path))

    memory = await orchestrator.run(
        AgentMemory(session_id="pipeline-test", question="Can multi-agent research systems reduce hallucinations?")
    )

    assert memory.subtasks
    assert memory.research_results
    assert memory.summaries
    assert memory.critic and memory.critic.assessments
    assert memory.report and "Executive Summary" in memory.report.markdown

