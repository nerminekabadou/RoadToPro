from __future__ import annotations
import asyncio
import json
import os
import pathlib
from typing import Dict, Any
from datetime import datetime
import orjson

DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "data")) / "ingestion"


async def to_jsonl(event: Dict[str, Any], filename: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    with path.open("ab") as f:
        f.write(orjson.dumps(event) + b"\n")


async def fanout_for_dashboard(event: Dict[str, Any]) -> None:
    # placeholder: integrate with your WS/Socket, Kafka, or DB
    # For now we just persist; your dashboard can tail this file.
    if event["type"].endswith("schedule.upsert"):
        await to_jsonl(event, "lol_schedule.jsonl")
    elif event["type"].endswith("result.upsert"):
        await to_jsonl(event, "lol_results.jsonl")
