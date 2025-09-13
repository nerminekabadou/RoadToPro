#!/usr/bin/env python3
"""
LoL Esports Live Telemetry (Unofficial) - quick tester
- Discovers live matches via LoLEsports persisted API (getLive/getEventDetails)
- Polls LiveStats "window" and/or "details" endpoints for the gameId(s)
Docs (unofficial):
  - getLive/getSchedule/getEventDetails (x-api-key header): https://esports-api.lolesports.com/persisted/gw/*
  - LiveStats window/details (no key): https://feed.lolesports.com/livestats/v1/{window|details}/{gameId}
"""

import argparse
import json
import os
import time
from typing import Any, Dict, Iterable, List, Optional
import urllib3

import requests

REL_BASE = "https://esports-api.lolesports.com/persisted/gw"
FEED_BASE = "https://feed.lolesports.com/livestats/v1"

# Disable SSL warnings if verification is disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SESSION = requests.Session()


# Configure SSL settings
def configure_ssl_session():
    """Configure the session with SSL settings to handle certificate issues."""
    # For development/testing: disable SSL verification
    # In production, you should properly configure certificates
    SESSION.verify = False
    print("Warning: SSL verification disabled for API requests")


# Configure SSL on session initialization
configure_ssl_session()


def _headers() -> Dict[str, str]:
    api_key = os.environ.get(
        "LOLESPORTS_API_KEY", "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
    ).strip()
    if not api_key:
        raise SystemExit("Missing LOLESPORTS_API_KEY environment variable.")
    return {"x-api-key": api_key}


def rel_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{REL_BASE}/{path}"
    params = params or {}
    params.setdefault("hl", "en-US")
    r = SESSION.get(url, headers=_headers(), params=params, timeout=15)

    if r.status_code == 403:
        print(f"[API Error] 403 Forbidden for {path}")
        print("This usually means:")
        print("  1. Invalid API key")
        print("  2. API key lacks permissions")
        print("  3. Rate limiting or API access restrictions")
        print(
            f"Current API key: {os.environ.get('LOLESPORTS_API_KEY', 'Using default key')[:20]}..."
        )
        print("\nTrying alternative approach...")
        return try_alternative_api(path, params)

    if r.status_code == 429:
        retry = int(r.headers.get("Retry-After", "2"))
        print(f"[rate-limit] 429 from {path}; sleeping {retry}s...")
        time.sleep(retry)
        r = SESSION.get(url, headers=_headers(), params=params, timeout=15)

    try:
        r.raise_for_status()
        return r.json()["data"]
    except requests.exceptions.HTTPError as e:
        print(f"[HTTP Error] {r.status_code} for {path}: {e}")
        print(f"Response: {r.text[:500]}")
        raise


def try_alternative_api(
    path: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Try alternative approaches when main API fails"""
    if path == "getLive":
        print("Cannot fetch live events without valid API key.")
        print("Please provide a valid LOLESPORTS_API_KEY environment variable.")
        print("You can:")
        print("  1. Set environment variable: set LOLESPORTS_API_KEY=your_key")
        print("  2. Use --test-gameids option with known game IDs")
        raise SystemExit("No alternative method available for live event discovery")
    else:
        raise SystemExit(f"No alternative method available for {path}")


def feed_get(kind: str, game_id: int) -> Dict[str, Any]:
    # kind: "window" or "details"
    url = f"{FEED_BASE}/{kind}/{game_id}"
    r = SESSION.get(url, timeout=15)
    if r.status_code == 404:
        raise RuntimeError(f"{kind} not available for game_id={game_id} (404)")
    r.raise_for_status()
    return r.json()


def discover_live_events() -> List[Dict[str, Any]]:
    """Return list of live 'events' (matches) with minimal fields."""
    data = rel_get("getLive")
    events = data.get("schedule", {}).get("events", [])
    # Flatten minimal
    slim = []
    for ev in events:
        m = ev.get("match") or {}
        league = ev.get("league") or {}
        slim.append(
            {
                "event_id": ev.get("id"),
                "startTime": ev.get("startTime"),
                "state": ev.get("state"),
                "match_id": (m or {}).get("id"),
                "teams": [t.get("name") for t in (m.get("teams") or [])],
                "league": league.get("slug") or league.get("name"),
            }
        )
    return slim


def match_to_game_ids(match_id: int) -> List[int]:
    data = rel_get("getEventDetails", params={"id": match_id})
    event = data.get("event") or {}
    match = event.get("match") or {}
    games = match.get("games") or []
    ids = []
    for g in games:
        try:
            ids.append(int(g.get("id")))
        except (TypeError, ValueError):
            pass
    return ids


def summarize_window(window: Dict[str, Any]) -> Dict[str, Any]:
    # Extract a compact summary from window JSON
    frames = window.get("frames", [])
    if not frames:
        return {"esportsGameId": window.get("esportsGameId"), "frames": 0}
    last = frames[-1]
    blue = last.get("blueTeam", {})
    red = last.get("redTeam", {})
    return {
        "esportsGameId": window.get("esportsGameId"),
        "frames": len(frames),
        "gameState": last.get("gameState"),
        "blue": {
            "kills": blue.get("totalKills"),
            "gold": blue.get("totalGold"),
            "towers": blue.get("towers"),
            "dragons": blue.get("dragons"),
            "barons": blue.get("barons"),
        },
        "red": {
            "kills": red.get("totalKills"),
            "gold": red.get("totalGold"),
            "towers": red.get("towers"),
            "dragons": red.get("dragons"),
            "barons": red.get("barons"),
        },
        "ts": last.get("rfc460Timestamp"),
    }


def stream_game(
    game_id: int,
    poll_kind: str = "window",
    interval: float = 2.0,
    out_jsonl: Optional[str] = None,
):
    """Continuously poll window/details for a single game id."""
    print(f"== Streaming {poll_kind} for game_id={game_id} (interval={interval}s) ==")
    f = open(out_jsonl, "a", encoding="utf-8") if out_jsonl else None
    try:
        while True:
            try:
                payload = feed_get(poll_kind, game_id)
                if poll_kind == "window":
                    summary = summarize_window(payload)
                    print(json.dumps(summary, ensure_ascii=False))
                    if f:
                        f.write(json.dumps({"type": "summary", "data": summary}) + "\n")
                else:
                    # details: dump only last frame + metadata sizes
                    frames = payload.get("frames", [])
                    last = frames[-1] if frames else {}
                    out = {
                        "frames_total": len(frames),
                        "last_ts": last.get("rfc460Timestamp"),
                        "last_participants": len(last.get("participants", []))
                        if last
                        else 0,
                    }
                    print(json.dumps(out, ensure_ascii=False))
                    if f:
                        f.write(json.dumps({"type": "details", "data": out}) + "\n")
            except Exception as e:
                print(f"[warn] {e}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        if f:
            f.close()


def main():
    ap = argparse.ArgumentParser(description="LoL Esports Live Telemetry tester")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--live",
        action="store_true",
        help="Auto-discover live events and pick first match",
    )
    g.add_argument(
        "--match-id",
        type=int,
        help="Poll a specific LoLEsports match id (auto-resolve to game ids)",
    )
    g.add_argument("--game-id", type=int, help="Poll a specific game id directly")
    ap.add_argument(
        "--kind",
        choices=["window", "details"],
        default="window",
        help="Which LiveStats endpoint to poll",
    )
    ap.add_argument(
        "--interval", type=float, default=2.0, help="Polling interval seconds"
    )
    ap.add_argument("--out", type=str, help="If set, append JSON lines to this file")
    args = ap.parse_args()

    if args.live:
        events = discover_live_events()
        if not events:
            raise SystemExit(
                "No live events right now. Try --match-id from getSchedule or use a different time."
            )
        ev = events[0]
        print(
            f"Picked live match: {ev['teams']} in {ev['league']} (match_id={ev['match_id']})"
        )
        game_ids = match_to_game_ids(int(ev["match_id"]))
    elif args.match_id is not None:
        game_ids = match_to_game_ids(args.match_id)
    else:
        game_ids = [args.game_id]

    if not game_ids:
        raise SystemExit("No game ids found for the selected match.")
    print(f"Game IDs: {game_ids}")
    # Just stream the first game id
    stream_game(
        game_ids[0], poll_kind=args.kind, interval=args.interval, out_jsonl=args.out
    )


if __name__ == "__main__":
    main()
