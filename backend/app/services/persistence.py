from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AgentLogRecord, ReportRecord, SessionRecord, SourceRecord, SubtaskRecord
from app.models.domain import AgentEvent, AgentMemory


class ResearchRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(self, memory: AgentMemory) -> None:
        self.db.add(SessionRecord(id=memory.session_id, question=memory.question, status="running"))
        await self.db.commit()

    async def save_event(self, event: AgentEvent) -> None:
        self.db.add(
            AgentLogRecord(
                session_id=event.session_id,
                agent=event.agent.value,
                status=event.status.value,
                message=event.message,
                elapsed_ms=event.elapsed_ms,
                payload=event.payload,
            )
        )
        await self.db.commit()

    async def save_memory(self, memory: AgentMemory, status: str = "completed") -> None:
        for subtask in memory.subtasks:
            await self.db.merge(
                SubtaskRecord(
                    id=subtask.id,
                    session_id=memory.session_id,
                    title=subtask.title,
                    query=subtask.query,
                    rationale=subtask.rationale,
                    status="completed",
                )
            )
        await self.db.flush()

        for result in memory.research_results:
            for source in result.sources:
                self.db.add(
                    SourceRecord(
                        session_id=memory.session_id,
                        subtask_id=result.subtask_id,
                        title=source.title,
                        url=source.url,
                        domain=source.domain,
                        domain_score=source.domain_score,
                        publish_date=source.publish_date,
                        content=source.content,
                    )
                )
        if memory.report:
            self.db.add(
                ReportRecord(
                    session_id=memory.session_id,
                    markdown=memory.report.markdown,
                    pdf_path=memory.report.pdf_path,
                    bibliography={"items": memory.report.bibliography},
                )
            )
        session = await self.db.get(SessionRecord, memory.session_id)
        if session:
            session.status = status
        await self.db.commit()

