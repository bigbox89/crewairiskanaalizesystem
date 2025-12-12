"""Configuration loader for Arbitr MCP server."""

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass
class Settings:
    api_key: str
    mode: str
    base_url: str
    timeout: float
    host: str
    port: int
    otel_endpoint: Optional[str]
    otel_service_name: str
    enable_metrics: bool

    @classmethod
    def from_env(cls) -> "Settings":
        mode = os.getenv("ARBITR_MODE", "test").lower()
        if mode not in ("test", "prod"):
            mode = "test"

        api_key = os.getenv("ARBITR_API_KEY", "")
        base_url = os.getenv("ARBITR_BASE_URL", "https://service.api-assist.com/parser/arbitr_api").rstrip("/")
        timeout = float(os.getenv("ARBITR_TIMEOUT", "15"))
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8080"))
        otel_endpoint = os.getenv("OTEL_ENDPOINT")
        otel_service_name = os.getenv("OTEL_SERVICE_NAME", "mcp-arbitr-api")
        enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() not in {"0", "false", "no"}

        if mode == "prod" and not api_key:
            raise ValueError("ARBITR_API_KEY is required in prod mode")

        return cls(
            api_key=api_key,
            mode=mode,
            base_url=base_url,
            timeout=timeout,
            host=host,
            port=port,
            otel_endpoint=otel_endpoint,
            otel_service_name=otel_service_name,
            enable_metrics=enable_metrics,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


