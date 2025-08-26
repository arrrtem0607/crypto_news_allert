import asyncio
from datetime import datetime, timezone

from fakeredis.aioredis import FakeRedis

from app.core import dedup
from app.core.models import NormalizedItem


def test_dedup_prevents_duplicates():
    fake = FakeRedis()
    dedup.init(client=fake)
    item = NormalizedItem(
        external_id="1",
        source="newsdata",
        title="Bitcoin rallies to $30k",
        summary="",
        url="https://example.com/a",
        published_at=datetime.now(timezone.utc),
    )
    fp = dedup.fingerprint(str(item.url), item.title, item.source)

    async def routine():
        assert not await dedup.is_duplicate(fp)
        await dedup.mark_seen(fp)
        assert await dedup.is_duplicate(fp)

    asyncio.run(routine())
