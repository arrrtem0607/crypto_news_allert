from __future__ import annotations

import hashlib
from datetime import datetime
import redis.asyncio as redis

_client: redis.Redis | None = None


def init(redis_url: str | None = None, client: redis.Redis | None = None) -> None:
    """Initialize the Redis client for de-duplication."""
    global _client
    if client is not None:
        _client = client
    elif redis_url:
        _client = redis.from_url(redis_url, decode_responses=True)
    else:
        raise ValueError("Provide redis_url or client")


def _key() -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"dedup:{today}"


def fingerprint(url: str | None, title: str, source: str) -> str:
    """Generate a fingerprint based on URL or title+source."""
    if url:
        return hashlib.sha1(url.encode()).hexdigest()
    base = f"{title.lower()}|{source}"
    return hashlib.sha1(base.encode()).hexdigest()


async def is_duplicate(fp: str) -> bool:
    assert _client is not None, "dedup.init() must be called first"
    return await _client.sismember(_key(), fp)


async def mark_seen(fp: str) -> None:
    assert _client is not None, "dedup.init() must be called first"
    key = _key()
    await _client.sadd(key, fp)
    # 24h TTL
    await _client.expire(key, 86400)
