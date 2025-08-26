import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from fakeredis.aioredis import FakeRedis
from zoneinfo import ZoneInfo

from app.core import dedup
from app.core.normalize import normalize_newsdata
from app.core.score import score_item
from app.core.config import FiltersSettings, ScoringSettings


class FakePublisher:
    def __init__(self):
        self.sent = []

    async def send(self, item, tz):
        self.sent.append(item)

def test_pipeline_dedup_once():
    fake = FakeRedis()
    dedup.init(client=fake)
    cfg = SimpleNamespace(
        filters=FiltersSettings(languages=["en"], exclude_domains=[]),
        scoring=ScoringSettings(
            w_source=1.0,
            w_recency=1.5,
            half_life_min=120,
            w_ticker=0.4,
            threshold=0.1,
        ),
    )
    now = datetime.now(timezone.utc)
    raw = {
        "article_id": "1",
        "title": "BTC rallies after ETF approval",
        "description": "",
        "link": "https://example.com/a",
        "pubDate": now.isoformat(),
        "language": "en",
    }
    pub = FakePublisher()

    async def process(r):
        item = normalize_newsdata(r)
        fp = dedup.fingerprint(str(item.url), item.title, item.source)
        score = score_item(item, datetime.now(timezone.utc), cfg)
        if score >= cfg.scoring.threshold and not await dedup.is_duplicate(fp):
            await pub.send(item, ZoneInfo("UTC"))
            await dedup.mark_seen(fp)

    asyncio.run(process(raw))
    asyncio.run(process(raw))
    assert len(pub.sent) == 1
