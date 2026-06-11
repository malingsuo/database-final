from __future__ import annotations

import logging
import os

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

TOKEN_TTL = 365 * 24 * 3600  # 1 year
_PREFIX = "token:"

_client: Redis | None = None


def _get_client() -> Redis:
    global _client
    if _client is None:
        _client = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True,
        )
    return _client


async def token_get(token: str) -> str | None:
    """Return cached account_id for token, or None on miss/error."""
    try:
        return await _get_client().get(f"{_PREFIX}{token}")
    except Exception as e:
        logger.warning("Redis get failed: %s", e)
        return None


async def token_set(token: str, account_id: str) -> None:
    try:
        await _get_client().set(f"{_PREFIX}{token}", account_id, ex=TOKEN_TTL)
    except Exception as e:
        logger.warning("Redis set failed: %s", e)


async def token_delete(token: str) -> None:
    try:
        await _get_client().delete(f"{_PREFIX}{token}")
    except Exception as e:
        logger.warning("Redis delete failed: %s", e)
