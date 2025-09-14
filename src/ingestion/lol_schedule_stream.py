from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Dict, Any, List, Optional

from .pandascore_client import PandaScoreClient
from .lol_normalizers import normalize_match, build_event
from ..core.bus import EventBus
from ..core.metrics import events_out

log = logging.getLogger(__name__)


class LolScheduleStream:
    """Polls upcoming & running LoL matches and publishes schedule-upserts."""

    def __init__(
        self,
        client: PandaScoreClient,
        bus: EventBus,
        poll_seconds: int = 60,
        leagues: Optional[List[str]] = None,
        pagesize: int = 50,
    ):
        self.client = client
        self.bus = bus
        self.poll_seconds = poll_seconds
        self.leagues = leagues
        self.pagesize = pagesize

    async def _drain_status(
        self,
        fetch_page: Callable[[int], Awaitable[List[Dict[str, Any]]]],
        seen_ids: set[int],
        status_label: str,
    ) -> None:
        """Page through one status (upcoming or running), publish, and de-dup within this tick."""
        page = 1
        while True:
            matches = await fetch_page(page)
            if not matches:
                break

            for m in matches:
                mid = m.get("id")
                if mid is None or mid in seen_ids:
                    continue  # avoid double-publish if it appears in both lists this tick
                seen_ids.add(mid)

                norm = normalize_match(m)
                ev = build_event("lol.schedule.upsert", norm)
                await self.bus.publish(ev)
                events_out.labels("lol.schedule.upsert").inc()

            if len(matches) < self.pagesize:
                break
            page += 1

        log.debug("schedule poll: drained %s (pages=%s)", status_label, page)

    async def run(self):
        while True:
            try:
                # De-dup within a single polling tick
                seen_ids: set[int] = set()

                # Option A (simple, sequential)
                await self._drain_status(
                    lambda p: self.client.list_upcoming_matches_lol(
                        page=p, per_page=self.pagesize
                    ),
                    seen_ids,
                    "upcoming",
                )
                await self._drain_status(
                    lambda p: self.client.list_running_matches_lol(
                        page=p, per_page=self.pagesize
                    ),
                    seen_ids,
                    "running",
                )

                # --- If you prefer concurrency, replace the two awaits above with:
                # await asyncio.gather(
                #     self._drain_status(
                #         lambda p: self.client.list_upcoming_matches_lol(page=p, per_page=self.pagesize),
                #         seen_ids, "upcoming"
                #     ),
                #     self._drain_status(
                #         lambda p: self.client.list_running_matches_lol(page=p, per_page=self.pagesize),
                #         seen_ids, "running"
                #     ),
                # )
                # Note: using the same seen_ids set is safe because we only use it for membership checks/adds.

            except Exception as e:
                log.exception("Schedule poll failed: %s", e)

            await asyncio.sleep(self.poll_seconds)
