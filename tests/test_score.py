from types import SimpleNamespace
from datetime import datetime, timezone

from app.core.models import NormalizedItem
from app.core.score import score_item
from app.core.config import FiltersSettings, ScoringSettings


class Cfg(SimpleNamespace):
    filters = FiltersSettings(languages=["en"], exclude_domains=[])
    scoring = ScoringSettings(
        w_source=1.0,
        w_recency=1.5,
        half_life_min=120,
        w_ticker=0.4,
        threshold=1.8,
    )


def test_score_item_passes_threshold():
    item = NormalizedItem(
        external_id="1",
        source="newsdata",
        title="Bitcoin breaks above $30k for the first time in months",
        summary="",
        url="https://example.com/a",
        published_at=datetime.now(timezone.utc),
        language="en",
        tickers=["BTC"],
    )
    score = score_item(item, datetime.now(timezone.utc), Cfg)
    assert score > Cfg.scoring.threshold


def test_score_item_filters_short_title():
    item = NormalizedItem(
        external_id="2",
        source="newsdata",
        title="Short title",
        summary="",
        url="https://example.com/b",
        published_at=datetime.now(timezone.utc),
        language="en",
        tickers=[],
    )
    score = score_item(item, datetime.now(timezone.utc), Cfg)
    assert score == 0.0
