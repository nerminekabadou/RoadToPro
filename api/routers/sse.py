from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio, orjson
from ..kafka_bridge import hub_highlights


router = APIRouter(tags=["SSE"])


@router.get("/sse/highlights")
async def sse_highlights():
    q = hub_highlights.register()

    async def gen():
        try:
            while True:
                msg = await q.get()
                yield f"event: highlight\n" + "data: " + msg.decode() + "\n\n"
        finally:
            hub_highlights.unregister(q)

    return StreamingResponse(gen(), media_type="text/event-stream")
