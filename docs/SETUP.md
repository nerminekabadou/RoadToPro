
# Seneca — Ingestion & Realtime Serving (Hackathon Build)

This repo ingests esports data (PandaScore schedules/results + LoLEsports live), publishes to Kafka (Redpanda), stores in Postgres, runs a Highlights Agent, and serves everything via a FastAPI API + SSE/WebSocket for the frontend dashboard.

> **What’s working now**
> - **Ingestion:** PandaScore (schedule/results), LoLEsports live frames
> - **Processing:** Highlights Agent (baron/dragon/tower/first blood/multi‑kill/comeback)
> - **Event Bus:** Redpanda/Kafka topics
> - **Storage:** Postgres (raw_events, matches, results, highlights*)
> - **Serving:** FastAPI (REST) + SSE bridge for highlights (WS optional)
> - **Frontend:** React dashboard bootstrapped

---

## 1) Prereqs

- **Docker Desktop** (latest)
- **Python 3.11+** and **uv**
- **Node 18+** and **npm**
- (optional) `rpk` CLI for Redpanda (or use the Console UI container)

Install **uv** (pick one):
```bash
# macOS/Linux
pipx install uv  ||  pip install --user uv

# Windows (PowerShell)
python -m pip install --user uv
```

---

## 2) Install Python deps

From the repo root:
```bash
uv sync
```

> If you added the API/ingestion dependency groups in `pyproject.toml`, they’ll be resolved automatically by `uv sync`.

---

## 3) Bring up infra (Kafka + Postgres)

**Start containers** (from repo root):
```bash
# Note: -f flag precedes the file; then 'up -d --build'
docker compose -f docker/docker-compose.yaml up -d --build
```

> Expect Redpanda on **`localhost:19092`** (external listener) and Postgres mapped to **`localhost:55432`**.

**Create Kafka topics** (one‑time):
```bash
# Linux/macOS (bash) — from repo root
bash scripts/kafka_topics.sh

# Windows PowerShell (uses container rpk)
$cid = (docker ps --filter "ancestor=redpandadata/redpanda" --format '{{.ID}}')
docker exec -it $cid rpk topic create `
  esports.lol.schedule.upsert `
  esports.lol.result.upsert `
  esports.lol.live.window `
  esports.lol.live.details `
  esports.lol.highlights
```

---

## 4) Environment

Create a `.env` in repo root (values are examples):
```env
# Auth to data sources
PANDASCORE_TOKEN=ps_xxx
LOLESPORTS_API_KEY=ls_xxx

# Infra targets (host processes)
PG_DSN=postgresql://seneca:seneca@localhost:55432/seneca
KAFKA_BOOTSTRAP=localhost:19092

# API / metrics
API_KEY=dev
API_PREFIX=/api
PROM_PORT=9108
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```
> **Windows:** make sure you export env vars *in the same PowerShell* you run the app:
```powershell
$env:PANDASCORE_TOKEN="rpEUd7r7WOqmirBOTqIxeFnz3MgbqhwLjnGWwZb3paM2iNPm0cA"
$env:LOLESPORTS_API_KEY="0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
$env:PG_DSN="postgresql://seneca:seneca@localhost:55432/seneca"
$env:KAFKA_BOOTSTRAP="localhost:19092"
$env:API_KEY="dev"
```

---

## 5) Run the backend

### Option A (recommended): **Run ingestion + API** (two terminals)

**Terminal 1 — Ingestion & processors**
```bash
uv run main.py
```
- Publishes to Kafka topics: `esports.lol.schedule.upsert`, `esports.lol.result.upsert`, `esports.lol.live.window`, `esports.lol.live.details`
- Writes to Postgres: `raw_events`, `matches`, `results` (and if wired, `highlights`)

**Terminal 2 — API server**
```bash
uv run uvicorn api.app:app --reload --port 8088
```
- REST base: `http://localhost:8088/api`
- SSE highlights: `GET /api/sse/highlights`
- Health: `GET /api/health`

### Option B: **Just run ingestion**
```bash
uv run main.py
```
(Useful on headless box; you can still consume Kafka or query Postgres.)

### Option C: **Just run the API**
```bash
uv run uvicorn api.app:app --reload --port 8088
```
(Assumes the DB has data and Kafka is running for SSE.)

---

## 6) Run the frontend

From the repo root:
```bash
cd frontend
npm i
npm start
```
- App will connect to `http://localhost:8088/api` (adjust in your frontend `.env` if needed).

---

## 7) Verify it’s alive

**Kafka:**
```bash
# Consume a few schedule messages
CID=$(docker ps --filter "ancestor=redpandadata/redpanda" --format '{{.ID}}')
docker exec -it $CID rpk topic consume esports.lol.schedule.upsert -n 3
```

**Postgres:**
```bash
# With psql
psql "postgresql://seneca:seneca@localhost:55432/seneca" -c "select count(*) from matches;"
```

**API:**
```bash
curl -H "X-API-Key: dev" http://localhost:8088/api/health
curl -H "X-API-Key: dev" http://localhost:8088/api/matches/upcoming
```

**SSE (highlights):**
Open in a browser console:
```js
const es = new EventSource('http://localhost:8088/api/sse/highlights');
es.addEventListener('highlight', (e) => console.log('HL:', JSON.parse(e.data)));
```

---

## 8) What runs where

- **Host processes** (Python, API) talk to:
  - **Kafka** at `localhost:19092` (external listener)
  - **Postgres** at `localhost:55432`
- **Containers** talk to each other via service names (e.g., `redpanda:9092`, `seneca_pg:5432`).

> If you containerize the API later, switch `KAFKA_BOOTSTRAP` to `redpanda:9092` and `PG_DSN` to `postgresql://seneca:seneca@seneca_pg:5432/seneca`.

---

## 9) Troubleshooting

- **KafkaConnectionError (node 0):** your client used `localhost:9092` but broker advertises `redpanda:9092`. Use `KAFKA_BOOTSTRAP=localhost:19092` (dual listeners are set in compose).
- **Postgres InvalidPasswordError:** you’re connecting to host Postgres on `5432`. Use the mapped port `55432` and `PG_DSN=postgresql://seneca:seneca@localhost:55432/seneca`.
- **No live frames:** either no pro game is live *or* `LOLESPORTS_API_KEY` missing. Try `getLive` curl to confirm.
- **Windows + shell scripts:** run `bash scripts/kafka_topics.sh` from Git Bash/WSL, or use the PowerShell snippet above.

---

## 10) Endpoints cheat‑sheet (for FE)

- `GET /api/matches/upcoming` — Next 24h
- `GET /api/matches/live` — Running now
- `GET /api/matches/{match_id}` — Details
- `GET /api/highlights?match_id=...` — Agent highlights
- `GET /api/sse/highlights` — Realtime stream of highlights (SSE)

---

## 11) Scripts

- `scripts/kafka_topics.sh` — creates required topics
- `scripts/smoke_pandascore_lol.py` — optional smoke test for PandaScore endpoints

---

## 12) What’s next (post‑hackathon)

- Add `predictions` table + endpoint (`/api/predictions/{match_id}`)
- Compact live frames into `events` topic (kill/tower/dragon/baron) for lightweight consumers
- Containerize API (share Docker network with Redpanda/Postgres)
- Add Valorant/CS2 ingestors (schema already supports `game` column)

---

**Have fun, ship it!**

