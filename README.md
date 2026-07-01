# Multi-Agent AI Research System

Production-grade FastAPI + React system for trustworthy AI research workflows.

Architecture

The backend orchestrates five agents through `AgentOrchestrator` and a shared `AgentMemory` object:

1. **Planner Agent** decomposes a user question into 3-6 JSON subtasks.
2. **Research Agent** runs subtask web searches concurrently with `asyncio.gather()` through Tavily.
3. **Summarizer Agent** creates evidence summaries with inline `[Source N]` citations and data-gap flags.
4. **Critic Agent** checks claims against raw source text using sentence-transformers cosine similarity and flags contradictions.
5. **Report Agent** emits a structured Markdown report and attempts PDF export.

The API streams typed `AgentEvent` messages over WebSocket so the frontend can show live progress, timing, citations, and confidence badges.

Run

```bash
cp .env.example .env
docker compose up --build
```

Open the frontend at [http://localhost:5173](http://localhost:5173). The API is at [http://localhost:8000](http://localhost:8000).

Without `TAVILY_API_KEY`, the backend uses deterministic mock research sources so demos and tests still work.

Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

Database

PostgreSQL tables are created on startup:

- `sessions`
- `subtasks`
- `sources`
- `reports`
- `agent_logs`

The equivalent DDL is checked in at `backend/app/db/schema.sql`.


