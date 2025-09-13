from __future__ import annotations
import os
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from .rate_limiter import HourlyTokenBucket
from ..core.metrics import requests_total, requests_errors, latency
from .backoff import retryable

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    PANDASCORE_TOKEN: str
    # LOLESPORTS_API_KEY: str
    # RIOT_API_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True


class PandaScoreClient:
    def __init__(
        self,
        base_url: str,
        token: Optional[str] = "rpEUd7r7WOqmirBOTqIxeFnz3MgbqhwLjnGWwZb3paM2iNPm0cA",
        requests_per_hour: int = 950,
        timeout_s: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token or Settings().PANDASCORE_TOKEN  # type: ignore
        self.bucket = HourlyTokenBucket(requests_per_hour)
        self._client = httpx.AsyncClient(
            timeout=timeout_s, headers={"Accept": "application/json"}
        )

    def _with_auth(self, path: str, params: Dict[str, Any]) -> str:
        params = dict(params or {})
        params["token"] = self.token
        return f"{self.base_url}{path}?{urlencode(params, doseq=True)}"

    @retryable
    async def _get(self, endpoint: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        await self.bucket.take()
        url = self._with_auth(endpoint, params)
        label = endpoint.strip("/").replace("/", "_")
        requests_total.labels(label).inc()
        with latency.labels(label).time():
            r = await self._client.get(url)
        if r.status_code >= 400:
            requests_errors.labels(label, r.status_code).inc()
            log.warning("HTTP %s %s", r.status_code, url)
            r.raise_for_status()
        data = r.json()
        # PandaScore returns arrays for list endpoints
        return data

    async def list_upcoming_matches_lol(self, page: int = 1, per_page: int = 50):
        params = {"page": page, "per_page": per_page, "sort": "begin_at"}
        return await self._get("/lol/matches/upcoming", params)

    async def list_running_matches_lol(self, page: int = 1, per_page: int = 50):
        params = {"page": page, "per_page": per_page, "sort": "begin_at"}
        return await self._get("/lol/matches/running", params)

    async def list_past_matches_lol(
        self, page: int = 1, per_page: int = 50, since_iso: str | None = None
    ):
        params = {
            "page": page,
            "per_page": per_page,
            "sort": "-end_at",
            "filter[status]": "finished",
        }  # <-- only finished
        if since_iso:
            params["range[end_at]"] = f"{since_iso},"
        return await self._get("/lol/matches/past", params)

    async def get_tournaments_lol(
        self, page: int = 1, per_page: int = 50, whitelist: List[str] | None = None
    ):
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "sort": "-begin_at",
            "filter[videogame]": "lol",
        }
        if whitelist:
            params["filter[slug]"] = whitelist
        return await self._get("/tournaments", params)

    async def close(self):
        await self._client.aclose()
