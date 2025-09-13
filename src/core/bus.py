from __future__ import annotations
import asyncio
from typing import Any, Dict


class EventBus:
    """Simple async pub/sub. Replace with Kafka/PubSub later without changing producers."""

    def __init__(self):
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    async def publish(self, event: Dict[str, Any]) -> None:
        await self._queue.put(event)

    async def subscribe(self):
        while True:
            yield await self._queue.get()
