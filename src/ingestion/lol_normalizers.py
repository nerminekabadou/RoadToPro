from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Any, List


def _ts() -> datetime:
    return datetime.now(timezone.utc)


def normalize_match(m: Dict[str, Any]) -> Dict[str, Any]:
    # Input is as returned by PandaScore /matches
    # Output is a compact, dashboard-friendly shape (idempotent on id)
    opponents = m.get("opponents") or []

    def opp_name(i):
        try:
            return (opponents[i]["opponent"] or {}).get("name")
        except Exception:
            return None

    return {
        "id": m["id"],
        "slug": m.get("slug"),
        "name": m.get("name"),
        "status": m.get("status"),
        "league": (m.get("league") or {}).get("name")
        if isinstance(m.get("league"), dict)
        else None,
        "tournament": (m.get("tournament") or {}).get("name")
        if isinstance(m.get("tournament"), dict)
        else None,
        "best_of": m.get("number_of_games"),
        "begin_at": m.get("begin_at"),
        "scheduled_at": m.get("scheduled_at"),
        "opponent1": opp_name(0),
        "opponent2": opp_name(1),
        "serie_id": m.get("serie_id"),
        "tournament_id": m.get("tournament_id"),
        "live": (m.get("status") == "running"),
    }


def build_event(event_type: str, match_norm: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": event_type,
        "at": _ts().isoformat(),
        "key": f"match:{match_norm['id']}",
        "payload": match_norm,
        "source": "pandascore",
        "version": "1.0",
    }
