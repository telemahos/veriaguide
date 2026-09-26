"""JSON key/value store for wizard sessions and itineraries (Redis, in-memory fallback)."""
import json
import time
from typing import Any

from app.utils.logging_config import get_logger

logger = get_logger("ai_guide")

PREFIX = "aiguide:"


class MemoryStore:
    def __init__(self):
        self._data: dict[str, tuple[float, str]] = {}

    async def get(self, key: str) -> Any | None:
        entry = self._data.get(key)
        if not entry:
            return None
        expires, raw = entry
        if expires < time.time():
            self._data.pop(key, None)
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        self._data[key] = (time.time() + ttl, json.dumps(value))

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def incr(self, key: str, ttl: int) -> int:
        current = await self.get(key) or 0
        expires = self._data.get(key, (time.time() + ttl, ""))[0] if current else time.time() + ttl
        self._data[key] = (expires, json.dumps(current + 1))
        return current + 1


class RedisStore:
    """Uses the shared CacheService pool; falls back to memory if Redis is down."""

    def __init__(self):
        self._fallback = MemoryStore()

    async def _redis(self):
        from app.services.cache_service import CacheService

        return await CacheService.get_redis()

    async def get(self, key: str) -> Any | None:
        try:
            raw = await (await self._redis()).get(PREFIX + key)
            return json.loads(raw) if raw else None
        except Exception as exc:
            logger.warning(f"AI guide store get fallback: {exc}")
            return await self._fallback.get(key)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        try:
            await (await self._redis()).setex(PREFIX + key, ttl, json.dumps(value))
        except Exception as exc:
            logger.warning(f"AI guide store set fallback: {exc}")
            await self._fallback.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        try:
            await (await self._redis()).delete(PREFIX + key)
        except Exception:
            await self._fallback.delete(key)

    async def incr(self, key: str, ttl: int) -> int:
        try:
            redis = await self._redis()
            value = await redis.incr(PREFIX + key)
            if value == 1:
                await redis.expire(PREFIX + key, ttl)
            return int(value)
        except Exception:
            return await self._fallback.incr(key, ttl)


_store: MemoryStore | RedisStore = RedisStore()


def get_store():
    return _store


def set_store(store) -> None:
    global _store
    _store = store
