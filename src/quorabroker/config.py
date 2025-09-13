"""Configuration management for quorabroker services (src layout)."""
from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field

try:  # optional dotenv
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore


class Settings(BaseModel):  # type: ignore[misc]
    kafka_bootstrap_servers: str = Field(default="localhost:9092")
    request_topic: str = Field(default="quora.fetch.requests")
    parsed_topic: str = Field(default="quora.fetch.parsed")

    mongo_uri: Optional[str] = Field(default=None)
    mongo_db: str = Field(default="quorabroker")
    mongo_collection: str = Field(default="pages")

    http_timeout_seconds: float = Field(default=20.0, gt=0, le=300)
    user_agent: str = Field(default="quorabroker/0.1")

    enable_browser: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    @classmethod
    def load(cls) -> "Settings":
        if load_dotenv:  # pragma: no cover
            load_dotenv(override=False)
        env = os.getenv
        # Access defaults via model_fields to avoid attribute resolution issues during classmethod
        f = cls.model_fields  # type: ignore[attr-defined]
        defd = lambda name: f[name].default  # noqa: E731
        return cls(
            kafka_bootstrap_servers=env("KAFKA_BOOTSTRAP_SERVERS", str(defd("kafka_bootstrap_servers"))),
            request_topic=env("REQUEST_TOPIC", str(defd("request_topic"))),
            parsed_topic=env("PARSED_TOPIC", str(defd("parsed_topic"))),
            mongo_uri=env("MONGO_URI") or None,
            mongo_db=env("MONGO_DB", str(defd("mongo_db"))),
            mongo_collection=env("MONGO_COLLECTION", str(defd("mongo_collection"))),
            http_timeout_seconds=float(env("HTTP_TIMEOUT_SECONDS", str(defd("http_timeout_seconds")))),
            user_agent=env("USER_AGENT", str(defd("user_agent"))),
            enable_browser=env("ENABLE_BROWSER", "false").lower() == "true",
            log_level=env("LOG_LEVEL", str(defd("log_level"))).upper(),
        )

settings = Settings.load()
