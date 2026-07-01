from pydantic import BaseModel, Field

from app.models.domain import AgentMemory


class ResearchRequest(BaseModel):
    question: str = Field(min_length=8, max_length=2000)


class ResearchStartResponse(BaseModel):
    session_id: str
    websocket_url: str


class ResearchResultResponse(BaseModel):
    session: AgentMemory

