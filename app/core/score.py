from __future__ import annotations

import math
from datetime import datetime
from fnmatch import fnmatch
from urllib.parse import urlparse

from .models import NormalizedItem


class ConfigLike:  # for type checking; actual Config defined in config.py
    class Filters:  # minimal stub
        languages: list[str]
        exclude_domains: list[str]
    class Scoring:
        w_source: float
        w_recency: float
        half_life_min: float
        w_ticker: float
        threshold: float


def score_item(item: NormalizedItem, now_utc: datetime, cfg: ConfigLike) -> float:
    """Return score for ``item``; items failing filters score ``0``."""

    # Filter: language
    if item.language and item.language not in cfg.filters.languages:
        return 0.0
    # Filter: domain blacklist
    domain = urlparse(str(item.url)).netloc.lower()
    for pattern in cfg.filters.exclude_domains:
        if fnmatch(domain, pattern):
            return 0.0
    # Filter: minimal title length
    if len(item.title) < 20:
        return 0.0

    age_min = (now_utc - item.published_at).total_seconds() / 60
    score = cfg.scoring.w_source
    score += cfg.scoring.w_recency * math.exp(-age_min / cfg.scoring.half_life_min)
    score += cfg.scoring.w_ticker * len(item.tickers)
    return score
