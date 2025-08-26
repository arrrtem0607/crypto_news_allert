from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from dateutil import parser

from .base import BaseProvider


class NewsdataProvider(BaseProvider):
    """Provider adapter for Newsdata.io."""

    name = "newsdata"

    def _build_request(self) -> Mapping[str, Any]:
        url = "https://newsdata.io/api/1/news"
        params = {"apikey": self.config.get("api_key")}
        query = self.config.get("query")
        if query:
            for part in query.split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    params.setdefault(k, v)
        return {"url": url, "params": params}

    async def _parse_items(self, data: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        results = []
        for item in data.get("results", []):
            url = item.get("link") or item.get("url")
            external_id = item.get("article_id") or item.get("id")
            if not external_id and url:
                external_id = hashlib.sha1(url.encode()).hexdigest()
            published = item.get("pubDate") or item.get("published_at")
            if published:
                try:
                    published_dt = parser.parse(published).astimezone(timezone.utc)
                except Exception:
                    published_dt = datetime.now(timezone.utc)
            else:
                published_dt = datetime.now(timezone.utc)
            new_item = dict(item)
            new_item["external_id"] = external_id
            new_item["pubDate"] = published_dt.isoformat()
            results.append(new_item)
        return results
