from __future__ import annotations
import asyncio, json, os, time, logging, logging.config, hashlib
from typing import Any, Dict, Optional, Tuple
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import orjson
import yaml
import asyncpg
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("lol_highlights")


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def jhash(obj: Any) -> str:
    return hashlib.md5(orjson.dumps(obj)).hexdigest()


# -------- safe getters (schema-tolerant for LoL Esports frames) --------
def g(d: Dict[str, Any], path: str, default=None):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def pick(d: Dict[str, Any], candidates: list[str], default=None):
    for p in candidates:
        v = g(d, p, None)
        if v is not None:
            return v
    return default


# Canonical field candidates in window frames (tolerant to minor schema shifts)
PATHS = {
    "game_state": ["gameState", "gameMetadata.gameState"],
    "timestamp": [
        "rfc460Timestamp",
        "gameMetadata.ESportsGameId",
    ],  # first is ISO; second fallback
    "blue_name": ["blueTeam.name", "gameMetadata.blueTeamName"],
    "red_name": ["redTeam.name", "gameMetadata.redTeamName"],
    "blue_kills": ["blueTeam.totalKills", "blueTeam.kills", "blueTeam.score.kills"],
    "red_kills": ["redTeam.totalKills", "redTeam.kills", "redTeam.score.kills"],
    "blue_gold": ["blueTeam.totalGold", "blueTeam.gold.total", "blueTeam.score.gold"],
    "red_gold": ["redTeam.totalGold", "redTeam.gold.total", "redTeam.score.gold"],
    "blue_barons": [
        "blueTeam.barons",
        "blueTeam.objectives.baron",
        "blueTeam.score.barons",
    ],
    "red_barons": [
        "redTeam.barons",
        "redTeam.objectives.baron",
        "redTeam.score.barons",
    ],
    "blue_dragons": [
        "blueTeam.dragons",
        "blueTeam.objectives.dragon.total",
        "blueTeam.score.dragons",
    ],
    "red_dragons": [
        "redTeam.dragons",
        "redTeam.objectives.dragon.total",
        "redTeam.score.dragons",
    ],
    "blue_towers": [
        "blueTeam.towers",
        "blueTeam.objectives.tower",
        "blueTeam.score.towers",
    ],
    "red_towers": [
        "redTeam.towers",
        "redTeam.objectives.tower",
        "redTeam.score.towers",
    ],
    "blue_inhibs": [
        "blueTeam.inhibitors",
        "blueTeam.objectives.inhibitor",
        "blueTeam.score.inhibitors",
    ],
    "red_inhibs": [
        "redTeam.inhibitors",
        "redTeam.objectives.inhibitor",
        "redTeam.score.inhibitors",
    ],
}


# -------- state per game --------
class GameState:
    def __init__(self, game_id: str, cfg: dict):
        self.id = game_id
        self.last_ts_iso: Optional[str] = None
        self.teams: dict[str, Optional[str]] = {"blue": None, "red": None}
        self.counts = {
            "blue": {
                "kills": 0,
                "gold": 0,
                "barons": 0,
                "dragons": 0,
                "towers": 0,
                "inhibs": 0,
            },
            "red": {
                "kills": 0,
                "gold": 0,
                "barons": 0,
                "dragons": 0,
                "towers": 0,
                "inhibs": 0,
            },
        }
        self.cooldown_until: dict[str, float] = {}
        self.first_blood_emitted = False
        self.kill_buffer: list[Tuple[float, str]] = []  # [(epoch, side)]
        self.gold_window: list[Tuple[float, int]] = []  # [(epoch, blue_minus_red)]
        self.cfg = cfg

    def _on_cd(self, key: str) -> bool:
        return self.cooldown_until.get(key, 0.0) > time.time()

    def _arm_cd(self, key: str, seconds: int):
        self.cooldown_until[key] = time.time() + seconds


# -------- highlight rules --------
def build_highlight(game: GameState, kind: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "game_id": game.id,
        "kind": kind,
        "at": time.time(),
        "teams": game.teams,
        "meta": meta,
    }
    return payload


def detect_and_emit(prev: GameState, frame: Dict[str, Any], emit):
    cfg = prev.cfg
    # extract values with tolerant getters
    ts_iso = pick(frame, PATHS["timestamp"])
    b_name = str(pick(frame, PATHS["blue_name"], "Blue") or "Blue")
    r_name = str(pick(frame, PATHS["red_name"], "Red") or "Red")
    prev.teams["blue"], prev.teams["red"] = b_name, r_name

    def val(side: str, key: str, default=0):
        path_key = f"{side}_{key}"
        v = pick(frame, PATHS[path_key], default)
        if isinstance(v, (int, float, str)):
            try:
                return int(v)
            except (ValueError, TypeError):
                return 0
        return 0

    # read current snapshot
    cur = {
        "blue": {
            "kills": val("blue", "kills"),
            "gold": val("blue", "gold"),
            "barons": val("blue", "barons"),
            "dragons": val("blue", "dragons"),
            "towers": val("blue", "towers"),
            "inhibs": val("blue", "inhibs"),
        },
        "red": {
            "kills": val("red", "kills"),
            "gold": val("red", "gold"),
            "barons": val("red", "barons"),
            "dragons": val("red", "dragons"),
            "towers": val("red", "towers"),
            "inhibs": val("red", "inhibs"),
        },
    }

    # FIRST BLOOD
    if not prev.first_blood_emitted:
        if cur["blue"]["kills"] + cur["red"]["kills"] >= 1:
            side = "blue" if cur["blue"]["kills"] > 0 else "red"
            fb = build_highlight(
                prev, "first_blood", {"side": side, "team": prev.teams[side]}
            )
            emit(fb)
            prev.first_blood_emitted = True
            prev._arm_cd("first_blood", cfg["cooldowns_s"]["first_blood"])

    # MULTI-KILLS (team level heuristic within window)
    # push kill deltas into a buffer with timestamps
    for side in ("blue", "red"):
        dk = cur[side]["kills"] - prev.counts[side]["kills"]
        now = time.time()
        for _ in range(max(0, dk)):
            prev.kill_buffer.append((now, side))
    # expire old kills
    window = cfg["multikill_window_s"]
    cutoff = time.time() - window
    prev.kill_buffer = [(t, s) for (t, s) in prev.kill_buffer if t >= cutoff]
    # count per side in window
    for side in ("blue", "red"):
        k = sum(1 for (_, s) in prev.kill_buffer if s == side)
        if k >= 2 and not prev._on_cd(f"multikill_{side}"):
            kind = {
                2: "double_kill",
                3: "triple_kill",
                4: "quadra_kill",
                5: "penta_kill",
            }.get(min(k, 5), "multi_kill")
            emit(
                build_highlight(
                    prev,
                    kind,
                    {"side": side, "team": prev.teams[side], "kills_in_window": k},
                )
            )
            prev._arm_cd(f"multikill_{side}", cfg["cooldowns_s"]["multikill"])

    # OBJECTIVES (diffs)
    def diff_and_emit(key: str, kind: str, cd_key: str):
        for side in ("blue", "red"):
            delta = cur[side][key] - prev.counts[side][key]
            if delta > 0 and not prev._on_cd(f"{cd_key}_{side}"):
                emit(
                    build_highlight(
                        prev,
                        kind,
                        {"side": side, "team": prev.teams[side], "delta": delta},
                    )
                )
                prev._arm_cd(f"{cd_key}_{side}", cfg["cooldowns_s"][cd_key])

    diff_and_emit("barons", "baron_taken", "baron")
    # dragons: detect soul if 4th dragon for a side
    for side in ("blue", "red"):
        if cur[side]["dragons"] > prev.counts[side]["dragons"] and not prev._on_cd(
            f"dragon_{side}"
        ):
            new_total = cur[side]["dragons"]
            kind = "dragon_soul" if new_total >= 4 else "dragon_taken"
            emit(
                build_highlight(
                    prev,
                    kind,
                    {
                        "side": side,
                        "team": prev.teams[side],
                        "total_dragons": new_total,
                    },
                )
            )
            prev._arm_cd(f"dragon_{side}", cfg["cooldowns_s"]["dragon"])

    diff_and_emit("towers", "tower_taken", "tower")
    diff_and_emit("inhibs", "inhibitor_taken", "inhibitor")

    # ACE heuristic: +5 team kills within short window while opponent delta small
    # (very rough without per-event stream, good enough for highlights)
    for side, opp in (("blue", "red"), ("red", "blue")):
        dk_side = cur[side]["kills"] - prev.counts[side]["kills"]
        dk_opp = cur[opp]["kills"] - prev.counts[opp]["kills"]
        if dk_side >= 5 and dk_opp == 0 and not prev._on_cd(f"ace_{side}"):
            emit(build_highlight(prev, "ace", {"side": side, "team": prev.teams[side]}))
            prev._arm_cd(f"ace_{side}", cfg["cooldowns_s"]["ace"])

    # COMEBACK spike: gold diff flip or big swing in short window
    diff = cur["blue"]["gold"] - cur["red"]["gold"]
    now = time.time()
    prev.gold_window.append((now, diff))
    # keep only recent points
    ccut = now - cfg["comeback_window_s"]
    prev.gold_window = [(t, d) for (t, d) in prev.gold_window if t >= ccut]
    if len(prev.gold_window) >= 2:
        t0, d0 = prev.gold_window[0]
        if (
            (d0 <= 0 < diff)
            or (d0 >= 0 > diff)
            or (abs(diff - d0) >= cfg["comeback_swing_gold"])
        ):
            if not prev._on_cd("comeback"):
                emit(build_highlight(prev, "comeback_swing", {"from": d0, "to": diff}))
                prev._arm_cd("comeback", cfg["cooldowns_s"]["dragon"])

    # store snapshot
    prev.last_ts_iso = str(ts_iso) if ts_iso is not None else None
    prev.counts = cur


# -------- Postgres (optional raw landing for highlights) --------
class PGRaw:
    def __init__(self, dsn: Optional[str]):
        self.dsn = dsn
        self.pool = None

    async def init(self):
        if not self.dsn:
            return
        self.pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)
        async with self.pool.acquire() as c:
            await c.execute("""
            CREATE TABLE IF NOT EXISTS raw_events (
              id BIGSERIAL PRIMARY KEY,
              type TEXT NOT NULL,
              at TIMESTAMPTZ NOT NULL,
              key TEXT NOT NULL,
              source TEXT NOT NULL,
              version TEXT NOT NULL,
              payload JSONB NOT NULL,
              payload_hash BYTEA NOT NULL,
              received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              UNIQUE (type, key, payload_hash)
            );""")

    async def write(self, ev: Dict[str, Any]):
        if not self.pool:
            return
        phash = hashlib.sha256(orjson.dumps(ev["payload"])).digest()
        async with self.pool.acquire() as c:
            await c.execute(
                """INSERT INTO raw_events(type, at, key, source, version, payload, payload_hash)
                   VALUES ($1, to_timestamp($2), $3, $4, $5, $6, $7)
                   ON CONFLICT (type, key, payload_hash) DO NOTHING""",
                ev["type"],
                ev["at"],
                ev["key"],
                ev.get("source", "highlights"),
                ev.get("version", "1.0"),
                ev["payload"],
                phash,
            )


# -------- main agent --------
class HighlightsAgent:
    def __init__(self, cfg_path="config/agent_lol_highlights.yaml"):
        cfg = load_yaml(cfg_path)["agent"]
        self.game = cfg["game"]
        self.live_topic = cfg["live_topic"]
        self.out_topic = cfg["highlights_topic"]
        self.cfg = cfg
        self.bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

        # --- DEBUG: Hardcode DSN to isolate environment variable issue ---
        dsn = "postgresql://seneca:seneca@localhost:55432/seneca"
        log.info(f"Attempting to connect with hardcoded DSN: {dsn}")
        self.pg = PGRaw(dsn)
        # self.pg = PGRaw(os.getenv("PG_DSN"))  # Original line

        self.producer: AIOKafkaProducer | None = None
        self.consumer: AIOKafkaConsumer | None = None
        self.games: dict[str, GameState] = {}

    async def start(self):
        await self.pg.init()
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap,
            acks="all",
            enable_idempotence=True,
            compression_type="lz4",
            linger_ms=10,
        )
        if self.producer is not None:
            await self.producer.start()
        self.consumer = AIOKafkaConsumer(
            self.live_topic,
            bootstrap_servers=self.bootstrap,
            enable_auto_commit=True,
            auto_offset_reset="latest",
            value_deserializer=lambda v: v,
            key_deserializer=lambda k: k,
            consumer_timeout_ms=0,
        )
        if self.consumer is not None:
            await self.consumer.start()
        log.info(
            "HighlightsAgent started; in=%s out=%s", self.live_topic, self.out_topic
        )

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()

    async def _emit(self, game_id: str, highlight: Dict[str, Any]):
        ev = {
            "type": f"{self.game}.highlight",
            "at": time.time(),
            "key": f"highlight:{game_id}:{highlight['kind']}",
            "payload": highlight,
            "source": "highlights",
            "version": "1.0",
        }
        if self.producer is not None:
            await self.producer.send_and_wait(
                self.out_topic, key=str(game_id).encode(), value=orjson.dumps(ev)
            )
        await self.pg.write(ev)

    async def run(self):
        try:
            await self.start()
            if self.consumer is None:
                log.error("Kafka consumer not initialized.")
                return
            async for msg in self.consumer:
                try:
                    if msg.value is None:
                        continue
                    env = orjson.loads(msg.value)
                    payload = env.get("payload") or {}
                except Exception:
                    # maybe raw frames without envelope
                    if msg.value is None:
                        continue
                    payload = orjson.loads(msg.value)
                game_id = (msg.key or b"").decode("utf-8")
                if not game_id:
                    # try to pull from envelope if key missing
                    env = orjson.loads(msg.value)
                    game_id = env.get("key", "").split(":")[-1]
                # parse envelope → payload (window frame batch)

                # choose the last frame to diff against
                frames = payload.get("frames") or []
                if not frames:
                    continue
                frame = frames[-1]

                state = self.games.get(game_id)
                if not state:
                    state = GameState(game_id, self.cfg)
                    self.games[game_id] = state

                await asyncio.get_running_loop().run_in_executor(
                    None,
                    detect_and_emit,
                    state,
                    frame,
                    lambda h: asyncio.run(self._emit(game_id, h)),
                )
        finally:
            await self.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    try:
        asyncio.run(HighlightsAgent().run())
    except KeyboardInterrupt:
        pass
