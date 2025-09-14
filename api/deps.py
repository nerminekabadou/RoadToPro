# api/deps.py
from __future__ import annotations

import os
import base64
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Optional, Tuple

import asyncpg
from contextlib import asynccontextmanager
from fastapi import Depends, Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("api.deps")


# -----------------------------
# Settings
# -----------------------------
@dataclass(slots=True)
class Settings:
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    api_key: str = os.getenv("API_KEY", "")  # empty => auth disabled
    cors_origins: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]
    pg_dsn: str | None = os.getenv("PG_DSN")
    kafka_bootstrap: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:19092")
    default_tz: str = os.getenv("DEFAULT_TZ", "UTC")


_settings = Settings()


def get_settings() -> Settings:
    return _settings


# -----------------------------
# DB pool (asyncpg)
# -----------------------------
class DB:
    def __init__(self, dsn: Optional[str]):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def init(self) -> None:
        if not self.dsn:
            log.warning("DB: PG_DSN not set; API will run without Postgres access")
            return
        if self.pool:
            return
        self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=8)
        log.info("DB: connected")

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        if not self.pool:
            raise RuntimeError("DB pool not initialized. Did you call await db.init()?")
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)

    async def fetch(self, sql: str, *args):
        async with self.acquire() as c:
            return await c.fetch(sql, *args)

    async def fetchrow(self, sql: str, *args):
        async with self.acquire() as c:
            return await c.fetchrow(sql, *args)

    async def fetchval(self, sql: str, *args):
        async with self.acquire() as c:
            return await c.fetchval(sql, *args)


_db = DB(_settings.pg_dsn)


async def get_db() -> DB:
    # lazy init on first dependency use
    if _db.pool is None and _db.dsn:
        await _db.init()
    return _db


# -----------------------------
# Auth (optional API key)
# -----------------------------
async def require_api_key(
    settings: Settings = Depends(get_settings),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> None:
    if not settings.api_key:
        return  # auth disabled
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


# -----------------------------
# Pagination helpers (cursor)
# cursor is base64url(JSON) -> {"last": <opaque>}
# -----------------------------
def encode_cursor(obj: dict) -> str:
    raw = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor: Optional[str]) -> dict:
    if not cursor:
        return {}
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def apply_pagination_sql(
    base_sql: str,
    id_column: str = "match_id",
    limit: int = 50,
    cursor: Optional[str] = None,
    direction: str = ">",
) -> Tuple[str, list]:
    """
    Appends WHERE + ORDER BY + LIMIT for keyset pagination on a numeric id column.
    Returns (sql, params). Expects caller to pass params to asyncpg.
    """
    params: list = []
    cur = decode_cursor(cursor)
    where = ""
    if "last" in cur:
        where = f" WHERE {id_column} {direction} $1"
        params.append(cur["last"])
    order = f" ORDER BY {id_column} ASC"
    limit_clause = f" LIMIT {max(1, min(500, limit))}"
    return base_sql + where + order + limit_clause, params


def next_cursor_from_rows(rows, id_field: str = "id") -> Optional[str]:
    if not rows:
        return None
    last = rows[-1][id_field]
    try:
        last = int(last)
    except Exception:
        pass
    return encode_cursor({"last": last})


# -----------------------------
# Time helpers
# -----------------------------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


# -----------------------------
# Small utils
# -----------------------------
def record_to_dict(rec: asyncpg.Record) -> dict:
    return dict(rec)


# Dependencies for the API
