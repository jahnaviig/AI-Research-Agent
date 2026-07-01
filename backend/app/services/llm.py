import json
import re

from app.models.domain import Subtask


class PlannerLLM:
    """Deterministic planner fallback; swap with a hosted LLM in production."""

    async def plan(self, question: str, max_subtasks: int = 6) -> list[Subtask]:
        normalized = re.sub(r"\s+", " ", question).strip()
        lenses = [
            ("Background and definitions", "Establish core definitions, actors, and context."),
            ("Recent evidence", "Find recent empirical evidence, dates, and source credibility."),
            ("Competing viewpoints", "Identify disagreements, risks, and counterarguments."),
            ("Quantitative data", "Locate statistics, trend data, and benchmark numbers."),
            ("Implications", "Synthesize practical implications and future outlook."),
        ]
        count = min(max(3, min(max_subtasks, 5)), len(lenses))
        return [
            Subtask(
                title=title,
                query=f"{normalized} {title.lower()}",
                rationale=rationale,
            )
            for title, rationale in lenses[:count]
        ]


def as_planner_json(subtasks: list[Subtask]) -> str:
    return json.dumps([subtask.model_dump() for subtask in subtasks], indent=2)

