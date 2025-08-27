from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import aiohttp

from app.core.config import load_config
from app.core.normalize import normalize_newsdata, normalize_cryptopanic
from app.core import dedup
from app.core.score import score_item
from app.core.telegram import TelegramPublisher, NewsItem
from app.providers.newsdata import NewsdataProvider
from app.providers.cryptopanic import CryptoPanicProvider


async def main() -> None:
    load_dotenv()
    cfg = load_config()
    tz = ZoneInfo(cfg.runtime.tz)
    dedup.init(cfg.runtime.redis_url)

    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)

    async with aiohttp.ClientSession() as session:
        provider = CryptoPanicProvider(session, cfg.providers.cryptopanic.model_dump())
        publisher = TelegramPublisher(
            cfg.telegram.bot_token,
            cfg.telegram.channel_id,
            rate_limit=cfg.telegram.rate_limit_per_min,
        )

        async def producer():
            async for raw in provider.run():
                await queue.put(raw)

        async def consumer():
            while True:
                raw = await queue.get()
                try:
                    item = normalize_cryptopanic(raw)
                    fp = dedup.fingerprint(str(item.url), item.title, item.source)
                    if await dedup.is_duplicate(fp):
                        continue
                    score = score_item(item, datetime.now(timezone.utc), cfg)
                    #if score >= cfg.scoring.threshold:
                    news = NewsItem(
                        title=item.title,
                        summary=item.summary or "",
                        url=str(item.url),
                        source=item.source,
                        tickers=item.tickers,
                        published_at=item.published_at,
                    )
                    print(news)
                    await publisher.send(news, tz)
                    await dedup.mark_seen(fp)
                finally:
                    queue.task_done()

        await asyncio.gather(producer(), consumer())


if __name__ == "__main__":
    asyncio.run(main())
