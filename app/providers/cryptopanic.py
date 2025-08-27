from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping
import asyncio

from dateutil import parser

from .base import BaseProvider, logger


class CryptoPanicProvider(BaseProvider):
    """Provider adapter for the cryptopanic crypto endpoint."""

    name = "cryptopanic"

    def _build_request(self) -> Mapping[str, Any]:
        base_url = self.config.get("base_url", "https://cryptopanic.com/api/developer/v2")
        endpoint = self.config.get("endpoint", "posts/")
        url = f"{base_url}/{endpoint}"
        params: dict[str, Any] = {"auth_token": self.config.get("api_key")}
        query = self.config.get("query")
        if query:
            for part in query.split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    params.setdefault(k, v)
        # defaults
        #params.setdefault("removeduplicate", "1")
        #params.setdefault("size", "50")
        #if endpoint != "crypto" and params.get("category") == "cryptocurrency":
        #    raise ValueError("Use /api/1/crypto endpoint for cryptocurrency category")
        return {"url": url, "params": params}

    async def poll(self) -> Iterable[Mapping[str, Any]]:  # type: ignore[override]
        req = self._build_request()
        url = req["url"]
        base_params = req.get("params", {})
        items: list[Mapping[str, Any]] = []
        page: str | None = None
        while True:
            params = dict(base_params)
            if page:
                params["page"] = page
            try:
                async with self.session.get(url, params=params, timeout=self.timeout) as resp:
                    text = await resp.text()
                    if resp.status >= 400:
                        logger.error(
                            "%s HTTP %s %s params=%s body=%s",
                            self.name,
                            resp.status,
                            url,
                            params,
                            text,
                        )
                        resp.raise_for_status()
                    data = await resp.json()
            except Exception:
                delay = self._backoff.next()
                logger.exception("%s poll failed; retrying in %.1fs", self.name, delay)
                await asyncio.sleep(delay)
                return []
            items.extend(await self._parse_items(data))
            page = data.get("nextPage")
            if not page:
                self._backoff.reset()
                break
        return items

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
