"""Configuration management for quorabroker services.

Centralised Pydantic model shared by fetch and persist services.
"""
from __future__ import annotations

import os
from typing import Optional

try:
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("pydantic dependency missing") from exc

try:  # optional dotenv
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore


class Settings(BaseModel):  # type: ignore[misc]
    # Kafka
    kafka_bootstrap_servers: str = Field(default="localhost:9092")
    request_topic: str = Field(default="quora.fetch.requests")
    parsed_topic: str = Field(default="quora.fetch.parsed")

    # Mongo
    mongo_uri: Optional[str] = Field(default=None)
    mongo_db: str = Field(default="quorabroker")
    mongo_collection: str = Field(default="pages")

    # HTTP
    http_timeout_seconds: float = Field(default=20.0, gt=0, le=300)
    user_agent: str = Field(default="quorabroker/0.1")

    # Service behaviour
    enable_browser: bool = Field(default=False)

    # Logging
    log_level: str = Field(default="INFO")

    @classmethod
    def load(cls) -> "Settings":  # noqa: D401
        if load_dotenv:  # pragma: no cover
            load_dotenv(override=False)
        env = os.getenv
        return cls(
            kafka_bootstrap_servers=env("KAFKA_BOOTSTRAP_SERVERS", cls.kafka_bootstrap_servers),
            request_topic=env("REQUEST_TOPIC", cls.request_topic),
            parsed_topic=env("PARSED_TOPIC", cls.parsed_topic),
            mongo_uri=env("MONGO_URI") or None,
            mongo_db=env("MONGO_DB", cls.mongo_db),
            mongo_collection=env("MONGO_COLLECTION", cls.mongo_collection),
            http_timeout_seconds=float(env("HTTP_TIMEOUT_SECONDS", str(cls.http_timeout_seconds))),
            user_agent=env("USER_AGENT", cls.user_agent),
            enable_browser=env("ENABLE_BROWSER", "false").lower() == "true",
            log_level=env("LOG_LEVEL", cls.log_level).upper(),
        )


settings = Settings.load()
