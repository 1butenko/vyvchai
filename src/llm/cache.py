import hashlib
import json
from typing import Any, Dict, List, Optional

import redis.asyncio as redis  # type: ignore
import structlog

from src.core.config import get_settings

logger = structlog.get_logger()


class SemanticCache:
    """
    Semantic cache for LLM responses to reduce costs.
    Caches based on message hash.
    """

    def __init__(self):
        settings = get_settings()
        self.redis_client = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
        self.ttl = settings.REDIS_CACHE_TTL
        self.cache_prefix = "llm_cache:"

    def _generate_cache_key(
        self, messages: List[Dict[str, str]], model: str, temperature: float
    ) -> str:
        """Generate deterministic cache key."""
        # Create hash from messages + model + temperature
        data = {
            "messages": messages,
            "model": model,
            "temperature": round(
                temperature, 2
            ),  # Round to avoid float precision issues
        }

        hash_str = json.dumps(data, sort_keys=True)
        hash_key = hashlib.sha256(hash_str.encode()).hexdigest()[:16]

        return f"{self.cache_prefix}{hash_key}"

    async def get(
        self, messages: List[Dict[str, str]], model: str, temperature: float
    ) -> Optional[Dict[str, Any]]:
        """Get cached response."""
        key = self._generate_cache_key(messages, model, temperature)

        try:
            cached = await self.redis_client.get(key)

            if cached:
                logger.info("cache_hit", key=key)
                return json.loads(cached)
            else:
                logger.debug("cache_miss", key=key)
                return None

        except Exception as e:
            logger.error("cache_get_error", error=str(e))
            return None

    async def set(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        response: Dict[str, Any],
    ):
        """Cache response."""
        key = self._generate_cache_key(messages, model, temperature)

        try:
            await self.redis_client.setex(key, self.ttl, json.dumps(response))
            logger.debug("cache_set", key=key)

        except Exception as e:
            logger.error("cache_set_error", error=str(e))

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache by pattern."""
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor, match=f"{self.cache_prefix}{pattern}*", count=100
                )

                if keys:
                    await self.redis_client.delete(*keys)

                if cursor == 0:
                    break

            logger.info("cache_invalidated", pattern=pattern)

        except Exception as e:
            logger.error("cache_invalidate_error", error=str(e))


# Global cache
semantic_cache = SemanticCache()
