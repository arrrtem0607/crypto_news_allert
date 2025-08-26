from __future__ import annotations

import os
import yaml
from pydantic import BaseModel


class TelegramSettings(BaseModel):
    bot_token: str
    channel_id: str
    parse_mode: str = "HTML"
    rate_limit_per_min: int = 10


class ProviderSettings(BaseModel):
    enabled: bool = True
    api_key: str | None = None
    poll_interval_s: int = 45
    query: str | None = None


class ProvidersSettings(BaseModel):
    newsdata: ProviderSettings


class FiltersSettings(BaseModel):
    languages: list[str] = ["en", "ru"]
    exclude_domains: list[str] = []


class ScoringSettings(BaseModel):
    w_source: float = 1.0
    w_recency: float = 1.5
    half_life_min: float = 120.0
    w_ticker: float = 0.4
    threshold: float = 1.8


class RuntimeSettings(BaseModel):
    tz: str = "Europe/Berlin"
    redis_url: str = "redis://localhost:6379/0"


class Config(BaseModel):
    telegram: TelegramSettings
    providers: ProvidersSettings
    filters: FiltersSettings
    scoring: ScoringSettings
    runtime: RuntimeSettings


def load_config(path: str = "config.yaml") -> Config:
    """Load configuration from YAML with environment variable expansion."""
    with open(path) as fh:
        text = os.path.expandvars(fh.read())
        data = yaml.safe_load(text)
    return Config.model_validate(data)
