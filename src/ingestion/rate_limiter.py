import asyncio
import time


class HourlyTokenBucket:
    """Simple hour-window limiter: N tokens replenished per hour."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.tokens = capacity
        self.reset_at = time.monotonic() + 3600
        self._lock = asyncio.Lock()

    async def take(self, n: int = 1):
        async with self._lock:
            now = time.monotonic()
            if now >= self.reset_at:
                self.tokens = self.capacity
                self.reset_at = now + 3600
            while self.tokens < n:
                # sleep until reset; you *could* be fancier (spread load), but this keeps us safe
                await asyncio.sleep(max(self.reset_at - time.monotonic(), 0.1))
                now = time.monotonic()
                if now >= self.reset_at:
                    self.tokens = self.capacity
                    self.reset_at = now + 3600
            self.tokens -= n
