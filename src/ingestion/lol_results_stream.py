from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from .pandascore_client import PandaScoreClient
from .lol_normalizers import normalize_match, build_event
from ..core.bus import EventBus
from ..core.metrics import events_out

log = logging.getLogger(__name__)


class LolResultsStream:
    """Polls recently finished LoL matches and publishes result-upserts."""

    def __init__(
        self,
        client: PandaScoreClient,
        bus: EventBus,
        poll_seconds: int = 90,
        pagesize: int = 50,
    ):
        self.client = client
        self.bus = bus
        self.poll_seconds = poll_seconds
        self.pagesize = pagesize
        self._since_iso: Optional[str] = (
            None  # ISO lower bound on end_at to reduce traffic
        )

    async def run(self):
        while True:
            try:
                page = 1
                got_any = False
                while True:
                    matches = await self.client.list_past_matches_lol(
                        page=page, per_page=self.pagesize, since_iso=self._since_iso
                    )

                    if not matches:
                        break
                    got_any = True
                    for m in matches:
                        norm = normalize_match(m)
                        ev = build_event("lol.result.upsert", norm)
                        await self.bus.publish(ev)
                        events_out.labels("lol.result.upsert").inc()
                    if len(matches) < self.pagesize:
                        break
                    page += 1
                # move the window up if we saw data
                if got_any:
                    # advance lower bound to now minus 1h to be safe with late updates
                    self._since_iso = (
                        datetime.now(timezone.utc) - timedelta(hours=1)
                    ).isoformat()
            except Exception as e:
                log.exception("Results poll failed: %s", e)
            await asyncio.sleep(self.poll_seconds)
