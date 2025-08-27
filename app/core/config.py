from __future__ import annotations

import os
import yaml
from pydantic import BaseModel, SecretStr, field_validator


class TelegramSettings(BaseModel):
    bot_token: SecretStr
    channel_id: int | str
    parse_mode: str = "HTML"
    rate_limit_per_min: int = 10

    @field_validator("channel_id", mode="before")
    @classmethod
    def _coerce_channel(cls, v: str | int) -> str | int:
        if isinstance(v, str) and v.startswith("-") and v.lstrip("-").isdigit():
            return int(v)
        return v


class ProviderSettings(BaseModel):
    enabled: bool = True
    api_key: str | None = None
    poll_interval_s: int = 45
    query: str | None = None


class NewsdataSettings(ProviderSettings):
    endpoint: str = "developer/v2"
    query: str | None = (
        "language=en,ru&timeframe=90m&removeduplicate=1&size=50&q=ETF OR SEC OR hack OR listing"
    )

class CryptoPanicSettings(ProviderSettings):
    endpoint: str = "posts/"
    #query: str | None = (
    #    "language=en,ru&timeframe=90m&removeduplicate=1&size=50&q=ETF OR SEC OR hack OR listing"
    #)


class ProvidersSettings(BaseModel):
    newsdata: NewsdataSettings
    cryptopanic: CryptoPanicSettings


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
