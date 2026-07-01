from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import asyncio

from app.db.session import AsyncSessionLocal
from app.models.domain import AgentMemory
from app.schemas.api import ResearchRequest, ResearchStartResponse
from app.services.events import event_bus
from app.services.orchestrator import AgentOrchestrator
from app.services.persistence import ResearchRepository

router = APIRouter()
running_tasks: dict[str, asyncio.Task] = {}


@router.post("/research", response_model=ResearchStartResponse, status_code=202)
async def start_research(payload: ResearchRequest) -> ResearchStartResponse:
    session_id = str(uuid4())
    memory = AgentMemory(session_id=session_id, question=payload.question)
    task = asyncio.create_task(_run_pipeline(memory))
    task.add_done_callback(lambda _: running_tasks.pop(session_id, None))
    running_tasks[session_id] = task
    return ResearchStartResponse(session_id=session_id, websocket_url=f"/api/ws/sessions/{session_id}")


async def _run_pipeline(memory: AgentMemory) -> None:
    async with AsyncSessionLocal() as db:
        orchestrator = AgentOrchestrator(ResearchRepository(db))
        await orchestrator.run(memory)


@router.websocket("/ws/sessions/{session_id}")
async def stream_session(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    try:
        async for event in event_bus.subscribe(session_id):
            await websocket.send_json(event.model_dump(mode="json"))
            if event.status in {"completed", "failed", "partial"} and event.agent == "Report Agent":
                await websocket.close()
                return
    except WebSocketDisconnect:
        return
