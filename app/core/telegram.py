from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from html import escape
from typing import Iterable, Union, Any
from zoneinfo import ZoneInfo

from telegram import Bot
from telegram.constants import ParseMode

ChatId = Union[int, str]

@dataclass
class NewsItem:
    title: str
    summary: str
    url: str
    source: str
    tickers: Iterable[str]
    published_at: datetime

_MAX_SUMMARY_LEN = 500

def format_message(item: NewsItem, tz: ZoneInfo) -> str:
    local_time = item.published_at.astimezone(tz).strftime("%Y-%m-%d %H:%M")
    tickers = ", ".join(item.tickers) if item.tickers else "-"
    title = escape(item.title or "")
    summary = escape(item.summary or "")[:_MAX_SUMMARY_LEN]
    url = escape(item.url or "")
    source = escape(item.source or "")
    return (
        f"<b>⚡ {title}</b>\n"
        f"{summary}\n\n"
        f"<b>Tickers:</b> {tickers} | <b>Src:</b> {source} | <b>T:</b> {local_time}\n\n"
        f'<a href="{url}">Open source</a>'
    )

def _unwrap_secret(value: Any) -> str:
    # Поддержка pydantic.SecretStr и аналогов
    get_secret = getattr(value, "get_secret_value", None)
    return get_secret() if callable(get_secret) else str(value)

def _normalize_chat_id(chat_id: ChatId) -> ChatId:
    if isinstance(chat_id, str):
        s = chat_id.strip()
        if s.startswith("@") or s.startswith("http"):
            return s
        if s.lstrip("-").isdigit():
            try:
                return int(s)
            except ValueError:
                return s
        return s
    return chat_id

class TelegramPublisher:
    """Lightweight wrapper around telegram.Bot with rate limiting."""
    def __init__(self, bot_token: Union[str, Any], chat_id: ChatId, rate_limit: int = 10):
        self.bot = Bot(_unwrap_secret(bot_token))  # <<< разворачиваем SecretStr
        self.chat_id: ChatId = _normalize_chat_id(chat_id)
        self.parse_mode = ParseMode.HTML
        self._semaphore = asyncio.Semaphore(rate_limit)

    async def send(self, item: NewsItem, tz: ZoneInfo) -> None:
        text = format_message(item, tz)
        async with self._semaphore:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=self.parse_mode,
            )
