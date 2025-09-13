import asyncio
import json
import websockets

TOKEN = "rpEUd7r7WOqmirBOTqIxeFnz3MgbqhwLjnGWwZb3paM2iNPm0cA"
FRAMES_URL = f"wss://live.pandascore.co/matches/595477?token={TOKEN}"
EVENTS_URL = f"wss://live.pandascore.co/matches/595477/events?token={TOKEN}"


async def consume(url):
    async with websockets.connect(url, max_size=None) as ws:
        async for msg in ws:
            data = json.loads(msg)
            print(data)  # TODO: normalize -> Kafka


asyncio.run(consume(FRAMES_URL))
# asyncio.run(consume(EVENTS_URL))  # run separately / in another task
