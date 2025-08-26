from datetime import timezone

from app.core.normalize import normalize_newsdata


def test_normalize_newsdata_basic():
    raw = {
        "article_id": "1",
        "title": "<b>BTC surges</b>",
        "description": "Bitcoin price soars",
        "link": "https://example.com/a",
        "pubDate": "2024-05-01T12:00:00Z",
        "language": "en",
        "creator": ["Alice"],
        "category": ["markets"],
    }
    item = normalize_newsdata(raw)
    assert item.external_id == "1"
    assert item.title == "BTC surges"
    assert str(item.url) == "https://example.com/a"
    assert item.published_at.tzinfo == timezone.utc
    assert item.tickers == ["BTC"]
