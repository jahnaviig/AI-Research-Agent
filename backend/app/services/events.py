import asyncio
from collections import defaultdict

from app.models.domain import AgentEvent


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[AgentEvent]]] = defaultdict(set)
        self._history: dict[str, list[AgentEvent]] = defaultdict(list)

    async def publish(self, event: AgentEvent) -> None:
        self._history[event.session_id].append(event)
        subscribers = list(self._subscribers[event.session_id])
        for queue in subscribers:
            await queue.put(event)

    async def subscribe(self, session_id: str):
        queue: asyncio.Queue[AgentEvent] = asyncio.Queue()
        self._subscribers[session_id].add(queue)
        try:
            for event in self._history[session_id]:
                yield event
            while True:
                yield await queue.get()
        finally:
            self._subscribers[session_id].discard(queue)


event_bus = EventBus()
