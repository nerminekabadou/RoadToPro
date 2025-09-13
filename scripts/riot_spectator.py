#!/usr/bin/env python3
"""
Riot Spectator quick tester (official Riot API)
- Polls /lol/summoner/v4/summoners/by-name/{name} to get encryptedSummonerId
- Then polls /lol/spectator/v4/active-games/by-summoner/{id} every N seconds
Docs:
  - APIs list: https://developer.riotgames.com/apis
  - Spectator-V4: Active games by summoner
"""

import argparse
import os
import time
import json
import requests


def riot_get(url: str, params=None):
    key = os.environ.get(
        "RIOT_API_KEY", "RGAPI-35029ba5-888b-478f-82a9-44e2d75ccf93"
    ).strip()
    if not key:
        raise SystemExit("Missing RIOT_API_KEY environment variable.")
    headers = {"X-Riot-Token": key}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    if r.status_code == 429:
        retry = int(r.headers.get("Retry-After", "2"))
        print(f"[rate-limit] 429; sleeping {retry}s...")
        time.sleep(retry)
        r = requests.get(url, headers=headers, params=params, timeout=15)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def platform_base(platform: str) -> str:
    return f"https://{platform}.api.riotgames.com"


def main():
    ap = argparse.ArgumentParser(description="Riot Spectator live tester")
    ap.add_argument(
        "--platform",
        default="EUW1",
        help="Platform routing (e.g., EUW1, NA1, KR, EUN1)",
    )
    ap.add_argument("--summoner", required=True, help="Summoner name to follow")
    ap.add_argument(
        "--interval", type=float, default=3.0, help="Polling interval seconds"
    )
    args = ap.parse_args()

    base = platform_base(args.platform.upper())
    # 1) Summoner -> encrypted id
    s = riot_get(f"{base}/lol/summoner/v4/summoners/by-name/{args.summoner}")
    if not s:
        raise SystemExit("Summoner not found.")
    summ_id = s["id"]
    print(f"Following summoner '{s['name']}' ({summ_id}) on {args.platform}")

    # 2) Poll active game
    try:
        while True:
            active = riot_get(
                f"{base}/lol/spectator/v4/active-games/by-summoner/{summ_id}"
            )
            if active is None:
                print("Not currently in game.")
            else:
                # Print compact summary
                out = {
                    "gameMode": active.get("gameMode"),
                    "gameQueueConfigId": active.get("gameQueueConfigId"),
                    "mapId": active.get("mapId"),
                    "gameStartTime": active.get("gameStartTime"),
                    "participants": [
                        p.get("summonerName") for p in active.get("participants", [])
                    ],
                }
                print(json.dumps(out, ensure_ascii=False))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Stopped by user.")


if __name__ == "__main__":
    main()
