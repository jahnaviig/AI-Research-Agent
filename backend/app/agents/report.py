from pathlib import Path
from time import perf_counter

from markdown import markdown

from app.agents.base import BaseAgent, EventEmitter
from app.models.domain import AgentMemory, AgentName, AgentStatus, ReportArtifact


class ReportAgent(BaseAgent):
    name = AgentName.report

    def __init__(self, export_dir: str = "/tmp/research-reports") -> None:
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def run(self, memory: AgentMemory, emit_event: EventEmitter) -> AgentMemory:
        started = perf_counter()
        await self.emit(memory, emit_event, AgentStatus.running, "Writing final report", started)
        bibliography = self._bibliography(memory)
        report_md = self._markdown(memory, bibliography)
        pdf_path = self._export_pdf(memory.session_id, report_md)
        memory.report = ReportArtifact(markdown=report_md, pdf_path=pdf_path, bibliography=bibliography)
        await self.emit(
            memory,
            emit_event,
            AgentStatus.completed,
            "Report exported",
            started,
            memory.report.model_dump(),
        )
        return memory

    def _markdown(self, memory: AgentMemory, bibliography: list[str]) -> str:
        critic = memory.critic
        low_confidence = [
            item for item in (critic.assessments if critic else []) if item.confidence in {"LOW", "MEDIUM"}
        ]
        findings = "\n\n".join(
            f"### {summary.title}\n{summary.summary}\n\n"
            f"**Data gaps:** {', '.join(summary.data_gaps) if summary.data_gaps else 'None flagged.'}"
            for summary in memory.summaries
        )
        conflicts = "\n".join(f"- {item}" for item in (critic.contradictions if critic else [])) or "- None flagged."
        claim_flags = "\n".join(
            f"- **{item.confidence} ({item.score})** {item.claim}"
            for item in low_confidence
        ) or "- No low or medium confidence claims flagged."
        refs = "\n".join(f"- {entry}" for entry in bibliography)
        return f"""# Research Report

## Executive Summary
Question: **{memory.question}**

The system decomposed the question into {len(memory.subtasks)} subtasks, searched them in parallel, summarized evidence with citations, and semantically checked claims against raw source text before producing this report.

## Findings
{findings}

## Confidence Review
{claim_flags}

## Conflicts
{conflicts}

## Bibliography
{refs}
"""

    def _bibliography(self, memory: AgentMemory) -> list[str]:
        entries: list[str] = []
        seen: set[str] = set()
        for result in memory.research_results:
            for source in result.sources:
                if source.url in seen:
                    continue
                seen.add(source.url)
                date = source.publish_date or "n.d."
                entries.append(f"{source.title}. ({date}). {source.domain}. {source.url}")
        return entries

    def _export_pdf(self, session_id: str, report_md: str) -> str | None:
        html = markdown(report_md)
        pdf_path = self.export_dir / f"{session_id}.pdf"
        try:
            from weasyprint import HTML

            HTML(string=html).write_pdf(str(pdf_path))
            return str(pdf_path)
        except Exception:
            fallback = self.export_dir / f"{session_id}.html"
            fallback.write_text(html, encoding="utf-8")
            return None

