from __future__ import annotations
import os, httpx


class LoLEsports:
    def __init__(
        self,
        gw_base: str,
        feed_base: str,
        hl: str = "en-US",
        timeout=10.0,
        api_key: str | None = None,
    ):
        self.gw = gw_base.rstrip("/")
        self.feed = feed_base.rstrip("/")
        self.hl = hl
        self.api_key = api_key or os.getenv("LOLESPORTS_API_KEY", "")
        self.h = {"x-api-key": self.api_key} if self.api_key else {}
        self.http = httpx.AsyncClient(timeout=timeout, headers=self.h)

    async def get_live(self) -> dict:
        r = await self.http.get(f"{self.gw}/getLive", params={"hl": self.hl})
        r.raise_for_status()
        return r.json()

    async def get_event_details(self, match_id: str) -> dict:
        r = await self.http.get(
            f"{self.gw}/getEventDetails", params={"hl": self.hl, "id": match_id}
        )
        r.raise_for_status()
        return r.json()

    async def window(self, game_id: str, starting: str | None = None) -> dict:
        params = {"startingTime": starting} if starting else {}
        r = await self.http.get(f"{self.feed}/window/{game_id}", params=params)
        r.raise_for_status()
        return r.json()

    async def details(
        self,
        game_id: str,
        starting: str | None = None,
        participant_ids: str | None = None,
    ) -> dict:
        params = {}
        if starting:
            params["startingTime"] = starting
        if participant_ids:
            params["participantIds"] = participant_ids
        r = await self.http.get(f"{self.feed}/details/{game_id}", params=params)
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self.http.aclose()
