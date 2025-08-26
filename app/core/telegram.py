"""Telegram publishing utilities."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from html import escape
from typing import Iterable
from zoneinfo import ZoneInfo

from telegram import Bot
from telegram.constants import ParseMode


@dataclass
class NewsItem:
    """Minimal representation of a news item for publishing."""

    title: str
    summary: str
    url: str
    source: str
    tickers: Iterable[str]
    published_at: datetime


def format_message(item: NewsItem, tz: ZoneInfo) -> str:
    """Render a :class:`NewsItem` into an HTML message."""

    local_time = item.published_at.astimezone(tz).strftime("%Y-%m-%d %H:%M")
    tickers = ", ".join(item.tickers) if item.tickers else "-"
    title = escape(item.title)
    summary = escape(item.summary)[:500]
    url = escape(item.url)
    source = escape(item.source)
    return (
        f"<b>⚡ {title}</b>\n"
        f"{summary}\n\n"
        f"<b>Tickers:</b> {tickers} | <b>Src:</b> {source} | <b>T:</b> {local_time}\n\n"
        f'<a href="{url}">Open source</a>'
    )


class TelegramPublisher:
    """Lightweight wrapper around :class:`telegram.Bot` with rate limiting."""

    def __init__(self, bot_token: str, chat_id: str, rate_limit: int = 10):
        self.bot = Bot(bot_token)
        self.chat_id = chat_id
        self.parse_mode = ParseMode.HTML
        # Allow up to ``rate_limit`` messages concurrently.
        self._semaphore = asyncio.Semaphore(rate_limit)

    async def send(self, item: NewsItem, tz: ZoneInfo) -> None:
        """Send a news item to the configured Telegram chat."""

        text = format_message(item, tz)
        async with self._semaphore:
            await self.bot.send_message(self.chat_id, text, parse_mode=self.parse_mode)
