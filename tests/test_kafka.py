import asyncio
from aiokafka import AIOKafkaProducer


async def go():
    p = AIOKafkaProducer(bootstrap_servers="localhost:19092")
    await p.start()
    md = await p.client.fetch_all_metadata()  # proves we can talk to node id 0
    print("BROKERS:", [(b.nodeId, b.host, b.port) for b in md.brokers()])
    await p.stop()


asyncio.run(go())
