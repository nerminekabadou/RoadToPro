import asyncpg, os
from functools import lru_cache


class DB:
    pool: asyncpg.Pool | None = None

    async def init(self):
        if self.pool:
            return
        dsn = os.getenv("PG_DSN")
        self.pool = await asyncpg.create_pool(dsn, min_size=1, max_size=8)

    async def fetch(self, *args, **kwargs):
        if not self.pool:
            raise RuntimeError("Database pool is not initialized. Call 'init()' first.")
        async with self.pool.acquire() as c:
            return await c.fetch(*args, **kwargs)


db = DB()  # Database connection and session management
