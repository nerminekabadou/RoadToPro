# pyproject.toml deps: asyncpg = "^0.29"
from __future__ import annotations
import asyncio, os, hashlib, orjson
import asyncpg
from typing import Dict, Any
import logging

log = logging.getLogger(__name__)

DDL_FILES = ["sql/01_raw.sql", "sql/02_matches.sql", "sql/03_results.sql"]


def _hash_payload(payload: Dict[str, Any]) -> bytes:
    return hashlib.sha256(orjson.dumps(payload)).digest()


def _norm(m: Dict[str, Any]) -> Dict[str, Any]:
    # expects your normalize_match(m) output (already good); enrich IDs/slugs if you added them
    return {
        "game": "lol",
        "match_id": m["id"],
        "slug": m.get("slug"),
        "name": m.get("name"),
        "status": m.get("status"),
        "live": bool(m.get("live")),
        "best_of": m.get("best_of"),
        "league": m.get("league"),
        "league_id": m.get("league_id"),
        "league_slug": m.get("league_slug"),
        "tournament": m.get("tournament"),
        "tournament_id": m.get("tournament_id"),
        "tournament_slug": m.get("tournament_slug"),
        "serie_id": m.get("serie_id"),
        "opponent1_id": m.get("opponent1_id"),
        "opponent1_slug": m.get("opponent1_slug"),
        "opponent1": m.get("opponent1"),
        "opponent2_id": m.get("opponent2_id"),
        "opponent2_slug": m.get("opponent2_slug"),
        "opponent2": m.get("opponent2"),
        "scheduled_at": m.get("scheduled_at"),
        "begin_at": m.get("begin_at"),
        "end_at": m.get("end_at"),
    }


class PGSink:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.getenv(
            "PG_DSN", "postgresql://seneca:seneca@localhost:5432/seneca"
        )
        self.pool: asyncpg.Pool | None = None

    async def init(self):
        self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=4)
        if self.pool is None:
            raise RuntimeError("Failed to create PG pool")
        async with self.pool.acquire() as conn:
            for path in DDL_FILES:
                log.info(f"Executing DDL from {path}")
                sql = open(path, "r", encoding="utf-8").read()
                await conn.execute(sql)

    async def write_event(self, ev: Dict[str, Any]):
        assert self.pool is not None
        log.info(f"Writing event to PG: {ev.get('type')}")
        payload = ev["payload"]
        phash = _hash_payload(payload)
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # raw landing
                await conn.execute(
                    """INSERT INTO raw_events(type, at, key, source, version, payload, payload_hash)
                       VALUES ($1,$2,$3,$4,$5,$6,$7)
                       ON CONFLICT (type, key, payload_hash) DO NOTHING""",
                    ev["type"],
                    ev["at"],
                    ev["key"],
                    ev.get("source", "pandascore"),
                    ev.get("version", "1.0"),
                    payload,
                    phash,
                )

                # routing
                if ev["type"].endswith("schedule.upsert") or ev["type"].endswith(
                    "match.status"
                ):
                    m = _norm(payload)
                    await conn.execute(
                        """INSERT INTO matches(
                             game, match_id, slug, name, status, live, best_of,
                             league_id, league_slug, league,
                             tournament_id, tournament_slug, tournament,
                             serie_id,
                             opponent1_id, opponent1_slug, opponent1,
                             opponent2_id, opponent2_slug, opponent2,
                             scheduled_at, begin_at, end_at, updated_at
                           ) VALUES (
                             $1,$2,$3,$4,$5,$6,$7,
                             $8,$9,$10,
                             $11,$12,$13,
                             $14,
                             $15,$16,$17,
                             $18,$19,$20,
                             $21,$22,$23, now()
                           )
                           ON CONFLICT (match_id) DO UPDATE SET
                             slug=EXCLUDED.slug, name=EXCLUDED.name, status=EXCLUDED.status,
                             live=EXCLUDED.live, best_of=EXCLUDED.best_of,
                             league_id=EXCLUDED.league_id, league_slug=EXCLUDED.league_slug, league=EXCLUDED.league,
                             tournament_id=EXCLUDED.tournament_id, tournament_slug=EXCLUDED.tournament_slug, tournament=EXCLUDED.tournament,
                             serie_id=EXCLUDED.serie_id,
                             opponent1_id=EXCLUDED.opponent1_id, opponent1_slug=EXCLUDED.opponent1_slug, opponent1=EXCLUDED.opponent1,
                             opponent2_id=EXCLUDED.opponent2_id, opponent2_slug=EXCLUDED.opponent2_slug, opponent2=EXCLUDED.opponent2,
                             scheduled_at=EXCLUDED.scheduled_at, begin_at=EXCLUDED.begin_at, end_at=EXCLUDED.end_at,
                             updated_at=now()""",
                        m["game"],
                        m["match_id"],
                        m["slug"],
                        m["name"],
                        m["status"],
                        m["live"],
                        m["best_of"],
                        m["league_id"],
                        m["league_slug"],
                        m["league"],
                        m["tournament_id"],
                        m["tournament_slug"],
                        m["tournament"],
                        m["serie_id"],
                        m["opponent1_id"],
                        m["opponent1_slug"],
                        m["opponent1"],
                        m["opponent2_id"],
                        m["opponent2_slug"],
                        m["opponent2"],
                        m["scheduled_at"],
                        m["begin_at"],
                        m["end_at"],
                    )

                elif ev["type"].endswith("result.upsert"):
                    m = _norm(payload)
                    # ensure match row exists/updates core fields
                    await conn.execute(
                        """INSERT INTO matches (game, match_id, status, end_at, updated_at)
                           VALUES ($1,$2,$3,$4, now())
                           ON CONFLICT (match_id) DO UPDATE SET
                             status=EXCLUDED.status, end_at=EXCLUDED.end_at, updated_at=now()""",
                        m["game"],
                        m["match_id"],
                        m["status"],
                        m["end_at"],
                    )
                    # and upsert results
                    await conn.execute(
                        """INSERT INTO results(match_id, winner_id, forfeit, draw, end_at, updated_at)
                           VALUES ($1,$2,$3,$4,$5, now())
                           ON CONFLICT (match_id) DO UPDATE SET
                             winner_id=EXCLUDED.winner_id, forfeit=EXCLUDED.forfeit,
                             draw=EXCLUDED.draw, end_at=EXCLUDED.end_at, updated_at=now()""",
                        m["match_id"],
                        payload.get("winner_id"),
                        payload.get("forfeit"),
                        payload.get("draw"),
                        m["end_at"],
                    )
