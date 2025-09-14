from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio, orjson
from ..kafka_bridge import hub_highlights
from trainer import chat
from fastapi import APIRouter, Query
from trainer import chat


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


@router.get("/sse/chat")
async def sse_chat(query: str = Query(..., description="User question")):
    """
    Stream chatbot responses to the client using SSE.
    """
    async def gen():
        yield "event: start\ndata: Chatbot is thinking...\n\n"
        try:
            answer = await chat(query)
            # If you want token streaming, split `answer` here
            yield f"event: message\ndata: {answer}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"
        yield "event: end\ndata: done\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")