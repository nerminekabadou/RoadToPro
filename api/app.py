from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.deps import get_settings, get_db

settings = get_settings()
app = FastAPI(title="Seneca Esports API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.on_event("startup")
async def _startup():
    # ensure DB pool is ready (optional: will lazy-init on first use anyway)
    db = await get_db()
    if db.dsn:
        await db.init()
