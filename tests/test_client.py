import os, json, pathlib, httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["PANDASCORE_TOKEN"]
BASE = "https://api.pandascore.co"
OUT = pathlib.Path("data/ingestion")
OUT.mkdir(parents=True, exist_ok=True)


def get(url, **params):
    params["token"] = TOKEN
    with httpx.Client(timeout=10) as c:
        r = c.get(BASE + url, params=params)
        r.raise_for_status()
        return r.json()


# 1) Upcoming LoL matches (no realtime)
upcoming = get("/matches/upcoming", **{"filter[videogame]": "lol", "per_page": 5})
# 2) Recently finished LoL matches
finished = get(
    "/matches",
    **{
        "filter[status]": "finished",
        "filter[videogame]": "lol",
        "sort": "-end_at",
        "per_page": 5,
    },
)


def norm(m):
    opps = m.get("opponents") or []

    def name(i):
        try:
            return (opps[i]["opponent"] or {}).get("name")
        except:
            return None

    return {
        "id": m["id"],
        "status": m.get("status"),
        "league": (m.get("league") or {}).get("name")
        if isinstance(m.get("league"), dict)
        else None,
        "tournament": (m.get("tournament") or {}).get("name")
        if isinstance(m.get("tournament"), dict)
        else None,
        "begin_at": m.get("begin_at"),
        "scheduled_at": m.get("scheduled_at"),
        "best_of": m.get("number_of_games"),
        "opponent1": name(0),
        "opponent2": name(1),
    }


with (OUT / "lol_schedule.jsonl").open("ab") as f:
    for m in upcoming:
        f.write(
            (
                json.dumps({"type": "lol.schedule.upsert", "payload": norm(m)}) + "\n"
            ).encode()
        )

with (OUT / "lol_results.jsonl").open("ab") as f:
    for m in finished:
        f.write(
            (
                json.dumps({"type": "lol.result.upsert", "payload": norm(m)}) + "\n"
            ).encode()
        )

print(f"wrote {len(upcoming)} schedule and {len(finished)} results to {OUT}/")
