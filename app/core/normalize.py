from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urlparse

from dateutil import parser

from .models import NormalizedItem

# Simple dictionary of common tickers for extraction
TICKER_PATTERN = re.compile(
    r"\b(BTC|ETH|SOL|BNB|XRP|ADA|DOGE|DOT|ARB|OP|LINK|MATIC|LTC|XMR|SHIB)\b",
    re.IGNORECASE,
)


def _strip_html(text: str | None) -> str | None:
    if not text:
        return None
    return re.sub(r"<[^>]+>", "", text).strip()


def _extract_tickers(text: str) -> list[str]:
    return sorted({m.group(1).upper() for m in TICKER_PATTERN.finditer(text)})


def normalize_newsdata(raw: dict) -> NormalizedItem:
    """Normalize a Newsdata.io payload into :class:`NormalizedItem`."""

    title = _strip_html(raw.get("title", "")) or ""
    summary = _strip_html(raw.get("description") or raw.get("content"))
    url = raw.get("link") or raw.get("url") or ""
    published_str = raw.get("pubDate") or raw.get("published_at")
    published_at = (
        parser.parse(published_str).astimezone(timezone.utc)
        if published_str
        else datetime.now(timezone.utc)
    )
    language = raw.get("language")
    authors = raw.get("creator") or []
    if isinstance(authors, str):
        authors = [authors]
    categories = raw.get("category") or []
    if isinstance(categories, str):
        categories = [categories]
    tickers = raw.get("coin") or raw.get("tickers") or []
    if isinstance(tickers, str):
        tickers = [tickers]
    if not tickers:
        tickers = _extract_tickers(f"{title} {summary or ''}")
    external_id = raw.get("article_id") or raw.get("id")
    if not external_id:
        external_id = hashlib.sha1(url.encode()).hexdigest()
    source = raw.get("source_id") or raw.get("source")
    if not source:
        source = urlparse(url).netloc

    return NormalizedItem(
        external_id=external_id,
        source=source or "newsdata",
        title=title,
        summary=summary,
        url=url,
        published_at=published_at,
        language=language,
        authors=authors,
        tickers=tickers,
        categories=categories,
    )

def normalize_cryptopanic(raw: dict) -> NormalizedItem:
    """Normalize a cryptopanic payload into :class:`NormalizedItem`."""

    title = _strip_html(raw.get("title", "")) or ""
    summary = _strip_html(raw.get("description") or raw.get("content"))
    url = raw.get("link") or raw.get("url") or ""
    published_str = raw.get("pubDate") or raw.get("published_at")
    published_at = (
        parser.parse(published_str).astimezone(timezone.utc)
        if published_str
        else datetime.now(timezone.utc)
    )
    language = raw.get("language")
    authors = raw.get("creator") or []
    if isinstance(authors, str):
        authors = [authors]
    categories = raw.get("category") or []
    if isinstance(categories, str):
        categories = [categories]
    tickers = raw.get("coin") or raw.get("tickers") or []
    if isinstance(tickers, str):
        tickers = [tickers]
    if not tickers:
        tickers = _extract_tickers(f"{title} {summary or ''}")
    external_id = str(raw.get("article_id") or raw.get("id"))
    if not external_id:
        external_id = hashlib.sha1(url.encode()).hexdigest()
    source = raw.get("source_id") or raw.get("source")
    if not source:
        source = urlparse(url).netloc

    return NormalizedItem(
        external_id=external_id,
        source=source or "newsdata",
        title=title,
        summary=summary,
        url=url,
        published_at=published_at,
        language=language,
        authors=authors,
        tickers=tickers,
        categories=categories,
    )
