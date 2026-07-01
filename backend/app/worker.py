import asyncio
import os

from app.models.domain import AgentMemory
from app.services.orchestrator import AgentOrchestrator


async def main() -> None:
    question = os.getenv("RESEARCH_QUESTION", "What is the latest evidence on AI research agents?")
    session_id = os.getenv("SESSION_ID", "worker-local")
    await AgentOrchestrator().run(AgentMemory(session_id=session_id, question=question))


if __name__ == "__main__":
    asyncio.run(main())

