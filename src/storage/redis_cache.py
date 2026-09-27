"""Redis Cache and Distributed Session Lock Manager."""

import json
import logging
from typing import Any, Dict, Optional
import redis.asyncio as aioredis

from src.core.config import settings

logger = logging.getLogger("RedisCache")


class SessionCache:
    """Manages low-latency active world graph cache and session turn locks."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._memory_cache: Dict[str, Any] = {}

    async def connect(self):
        """Connects to Redis server if available."""
        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=2.0,
            )
            await self._redis.ping()
            logger.info("Connected to Redis at %s", settings.REDIS_URL)
        except Exception as e:
            logger.warning("Could not connect to Redis (%s). Using In-Memory Cache.", e)
            self._redis = None

    async def close(self):
        """Closes Redis connection."""
        if self._redis:
            await self._redis.close()

    async def get_graph(self, world_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached graph for world."""
        key = f"world_graph:{world_id}"
        if self._redis:
            try:
                val = await self._redis.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.error("Redis error in get_graph: %s", e)
        return self._memory_cache.get(key)

    async def set_graph(self, world_id: str, graph_dict: Dict[str, Any], ttl: int = 3600):
        """Caches active world graph."""
        key = f"world_graph:{world_id}"
        self._memory_cache[key] = graph_dict
        if self._redis:
            try:
                await self._redis.setex(key, ttl, json.dumps(graph_dict))
            except Exception as e:
                logger.error("Redis error in set_graph: %s", e)


session_cache = SessionCache()
