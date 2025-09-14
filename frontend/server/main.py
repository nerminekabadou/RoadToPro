# server/main.py
from fastapi import FastAPI, WebSocket
import asyncio, json, random
app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    minute = 0
    gold = 0
    while True:
        await asyncio.sleep(2)  # envoie toutes les 2s
        minute += 1
        gold += random.randint(-400, 500)
        p = 0.5 + gold / 4000.0
        p = max(0.0, min(1.0, p))
        msg = {
            "win_prob": {"blue": round(p, 3), "red": round(1 - p, 3)},
            "gold_diff": [{"minute": minute, "diff": gold}],
            "events": [{"time": f"{minute:02d}:00", "desc": random.choice(["Kill", "Tower", "Dragon", "First Blood"])}]
        }
        await ws.send_text(json.dumps(msg))
