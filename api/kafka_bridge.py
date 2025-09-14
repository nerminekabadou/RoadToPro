import asyncio, os, orjson
from aiokafka import AIOKafkaConsumer


class Hub:
    def __init__(self):
        self.queues = set()

    def register(self):
        q = asyncio.Queue(maxsize=1000)
        self.queues.add(q)
        return q

    def unregister(self, q):
        self.queues.discard(q)

    async def broadcast(self, msg: bytes):
        for q in list(self.queues):
            if not q.full():
                q.put_nowait(msg)


hub_highlights = Hub()


async def run_highlight_consumer():
    consumer = AIOKafkaConsumer(
        "esports.lol.highlights",
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "localhost:19092"),
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
    await consumer.start()
    try:
        async for msg in consumer:
            if msg.value is not None:
                await hub_highlights.broadcast(msg.value)
    finally:
        await consumer.stop()  # Bridge between Kafka topics and API (e.g., for SSE)
