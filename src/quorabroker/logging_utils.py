"""Logging configuration utilities."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import structlog  # type: ignore


@runtime_checkable
class LoggerLike(Protocol):
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: E701
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: E701
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...  # noqa: E701


def configure_logging(level: str) -> LoggerLike:  # type: ignore[override]
    structlog.configure(  # type: ignore[attr-defined]
        processors=[
            structlog.processors.add_log_level,  # type: ignore[attr-defined]
            structlog.processors.TimeStamper(fmt="iso"),  # type: ignore[attr-defined]
            structlog.processors.JSONRenderer(),  # type: ignore[attr-defined]
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog, level, structlog.INFO)
        ),  # type: ignore[attr-defined]
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger()  # type: ignore[attr-defined]
