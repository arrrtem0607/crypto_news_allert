from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, AnyUrl
from typing import List


class NormalizedItem(BaseModel):
    """Unified schema for news items after normalization."""

    external_id: str
    source: str
    title: str
    summary: str | None = None
    url: str
    published_at: datetime
    language: str | None = None
    authors: List[str] = []
    tickers: List[str] = []
    categories: List[str] = []
