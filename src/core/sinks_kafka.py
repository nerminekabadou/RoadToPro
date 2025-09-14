from __future__ import annotations
import os, asyncio, orjson, logging
from typing import Dict, Any
from aiokafka import AIOKafkaProducer

log = logging.getLogger(__name__)

TOPIC_MAP = {
    "lol.schedule.upsert": "esports.lol.schedule.upsert",
    "lol.match.status": "esports.lol.match.status",  # optional stream for canceled/postponed
    "lol.result.upsert": "esports.lol.result.upsert",
    "lol.live.window": "esports.lol.live.window",
    "lol.live.details": "esports.lol.live.details",
}


def _key_for(ev: Dict[str, Any]) -> bytes:
    # stable partitioning by match id → preserves order per match
    key = (ev.get("payload") or {}).get("id") or ev.get("key")
    return str(key).encode("utf-8")


def _value_for(ev: Dict[str, Any]) -> bytes:
    # send the whole envelope; downstream consumers can evolve without breaking
    return orjson.dumps(ev)


class KafkaSink:
    def __init__(self, bootstrap: str | None = None):
        self.bootstrap = bootstrap or os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
        self._producer: AIOKafkaProducer | None = None
        self._lock = asyncio.Lock()

    async def start(self):
        async with self._lock:
            if self._producer:
                return
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap,
                acks="all",
                enable_idempotence=True,
                linger_ms=20,
                compression_type="lz4",
                # max_in_flight_requests_per_connection=5,
                request_timeout_ms=15000,
            )
            await self._producer.start()
            log.info("KafkaSink connected to %s", self.bootstrap)

    async def stop(self):
        async with self._lock:
            if self._producer:
                await self._producer.stop()
                self._producer = None

    async def write_event(self, ev: Dict[str, Any]):
        topic = TOPIC_MAP.get(ev["type"])
        if not topic:
            return  # ignore other types
        if not self._producer:
            await self.start()
        assert self._producer
        await self._producer.send_and_wait(
            topic=topic,
            key=_key_for(ev),
            value=_value_for(ev),
        )
