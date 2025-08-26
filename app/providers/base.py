"""Base provider adapter with polling and backoff logic.

This module defines an abstract :class:`BaseProvider` that fetches data from
external news APIs.  Concrete providers should inherit from this class and
implement the :meth:`_build_request` and :meth:`_parse_items` hooks to convert
provider specific payloads into a list of normalized dictionaries.
"""

from __future__ import annotations

import abc
import asyncio
import json
import logging
import random
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import aiohttp


logger = logging.getLogger(__name__)


@dataclass
class Backoff:
    """Exponential backoff helper with jitter."""

    base: float = 1.0
    factor: float = 2.0
    max_delay: float = 60.0
    attempt: int = 0

    def next(self) -> float:
        self.attempt += 1
        delay = min(self.base * (self.factor ** (self.attempt - 1)), self.max_delay)
        # Add a little jitter to avoid thundering herds
        return delay + random.random()

    def reset(self) -> None:
        self.attempt = 0


class BaseProvider(abc.ABC):
    """Template base class for news providers.

    Subclasses only need to implement provider specific request building and
    response parsing.  The :meth:`poll` coroutine handles retry and backoff
    semantics and yields normalized items.
    """

    name: str = "base"

    def __init__(self, session: aiohttp.ClientSession, config: Mapping[str, Any]):
        self.session = session
        self.config = config
        self._backoff = Backoff()

    # ------------------------------------------------------------------
    # Configuration helpers
    @property
    def poll_interval(self) -> int:
        return int(self.config.get("poll_interval_s", 60))

    @property
    def timeout(self) -> int:
        return int(self.config.get("timeout_s", 5))

    # ------------------------------------------------------------------
    @abc.abstractmethod
    def _build_request(self) -> Mapping[str, Any]:
        """Return kwargs for :meth:`aiohttp.ClientSession.get`.

        Typically includes the request URL and query parameters.  API keys can
        be provided via headers or query params depending on the provider.
        """

    @abc.abstractmethod
    async def _parse_items(self, data: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        """Parse raw response data into an iterable of items."""

    # ------------------------------------------------------------------
    async def poll(self) -> Iterable[Mapping[str, Any]]:
        """Fetch a batch of items from the provider.

        The call is wrapped with basic exponential backoff in case of network
        errors or non-200 HTTP responses.
        """

        req = self._build_request()
        try:
            async with self.session.get(**req, timeout=self.timeout) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    logger.error(
                        "%s HTTP %s %s params=%s body=%s",
                        self.name,
                        resp.status,
                        req.get("url"),
                        req.get("params"),
                        text,
                    )
                    if (
                        resp.status == 422
                        and str(req.get("url", "")).endswith("/news")
                        and (req.get("params") or {}).get("category") == "cryptocurrency"
                    ):
                        logger.error(
                            "Newsdata returned 422 for /news with category=cryptocurrency. Use /api/1/crypto instead."
                        )
                    resp.raise_for_status()
                payload = json.loads(text) if text else {}
            self._backoff.reset()
            return await self._parse_items(payload)
        except Exception:
            delay = self._backoff.next()
            logger.exception("%s poll failed; retrying in %.1fs", self.name, delay)
            await asyncio.sleep(delay)
            return []

    # ------------------------------------------------------------------
    async def run(self):
        """Async generator yielding items on each poll cycle."""
        while True:
            items = await self.poll()
            for item in items:
                yield item
            await asyncio.sleep(self.poll_interval)
