from fastapi import APIRouter, Query
from ..db import db


router = APIRouter(tags=["Matches"])


@router.get("/matches")
async def list_matches(game: str = "lol", status: str | None = None, limit: int = 50):
    await db.init()
    where = ["game = $1"]
    params = [game]
    if status:
        where.append("status = $%d" % (len(params) + 1))
        params.append(status)
    sql = f"SELECT match_id AS id, game, name, status, best_of, league, tournament, scheduled_at, begin_at, start_time FROM matches WHERE {' AND '.join(where)} ORDER BY start_time NULLS LAST LIMIT {limit}"
    rows = await db.fetch(sql, *params)
    return {"data": [dict(r) for r in rows], "meta": {"count": len(rows)}}
