from __future__ import annotations
import asyncio, logging, itertools
from datetime import datetime, timezone
from typing import Dict, Any, Set

from .lolesports_client import LoLEsports
from ..core.bus import EventBus
from ..core.metrics import events_out

log = logging.getLogger(__name__)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LolLiveStream:
    """Discovers live games via getLive, then tails /window and /details incrementally."""

    def __init__(
        self,
        client: LoLEsports,
        bus: EventBus,
        discover_s: int = 20,
        window_s: int = 2,
        details_s: int = 5,
    ):
        self.client = client
        self.bus = bus
        self.discover_s = discover_s
        self.window_s = window_s
        self.details_s = details_s
        self.active: Set[str] = set()  # esportsGameId
        self._last_ts: Dict[str, str] = {}  # per game startingTime cursor

    async def _publish(self, ev_type: str, game_id: str, payload: Dict[str, Any]):
        ev = {
            "type": ev_type,
            "at": now_iso(),
            "key": f"lolesports:game:{game_id}",
            "payload": payload,
            "source": "lolesports",
            "version": "1.0",
        }
        await self.bus.publish(ev)
        events_out.labels(ev_type).inc()

    async def _tail_game(self, game_id: str):
        """Tail one game: call window fast, details slower. Stop when game ends (no new frames)."""
        last = self._last_ts.get(game_id)
        while game_id in self.active:
            try:
                win = await self.client.window(game_id, starting=last)
                await self._publish("lol.live.window", game_id, win)
                # advance cursor to last frame timestamp if any
                frames = (win or {}).get("frames") or []
                if frames:
                    last = frames[-1].get("rfc460Timestamp")
                    self._last_ts[game_id] = last
            except Exception as e:
                log.warning("window[%s] err: %s", game_id, e)

            # details less frequently (heavier)
            if int(datetime.now().timestamp()) % self.details_s == 0:
                try:
                    det = await self.client.details(game_id, starting=last)
                    await self._publish("lol.live.details", game_id, det)
                except Exception as e:
                    log.debug("details[%s] err: %s", game_id, e)

            await asyncio.sleep(self.window_s)

        log.info("stopped tailing game_id=%s", game_id)

    async def _discover_loop(self):
        """Refresh live games set."""
        while True:
            try:
                data = await self.client.get_live()
                # walk events → match → games, track only inProgress
                events = (((data or {}).get("data") or {}).get("schedule") or {}).get(
                    "events"
                ) or []
                live_game_ids = []
                for ev in events:
                    match = (ev or {}).get("match") or {}
                    games = match.get("games") or []
                    for g in games:
                        if g.get("state") in ("inProgress", "inProgressMedia"):
                            live_game_ids.append(g.get("id"))
                # activate/deactivate
                new = set(filter(None, live_game_ids))
                started = new - self.active
                ended = self.active - new
                for gid in started:
                    self.active.add(gid)
                    asyncio.create_task(self._tail_game(gid))
                    log.info("start tailing live game %s", gid)
                for gid in ended:
                    self.active.discard(gid)
                    log.info("mark game ended %s", gid)
            except Exception as e:
                log.exception("discover live failed: %s", e)
            await asyncio.sleep(self.discover_s)

    async def run(self):
        await self._discover_loop()
