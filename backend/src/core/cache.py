from __future__ import annotations

import json
import logging

import redis

from src.core.config import settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def cache_get(key: str) -> dict | None:
    try:
        raw = _get_client().get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning("Redis get failed: %s", e)
        return None


def cache_set(key: str, value: dict) -> None:
    try:
        _get_client().set(key, json.dumps(value, ensure_ascii=False))
    except Exception as e:
        logger.warning("Redis set failed: %s", e)


def cache_delete(key: str) -> None:
    try:
        _get_client().delete(key)
    except Exception as e:
        logger.warning("Redis delete failed: %s", e)
