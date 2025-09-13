"""Domain message models used across services."""
from __future__ import annotations

from typing import Optional

try:
    from pydantic import BaseModel, HttpUrl, Field
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("pydantic dependency missing") from exc


class FetchRequest(BaseModel):  # type: ignore[misc]
    url: HttpUrl
    id: Optional[str] = Field(default=None)


class ParsedPage(BaseModel):  # type: ignore[misc]
    url: HttpUrl
    id: Optional[str] = Field(default=None)
    question: Optional[str] = None
    answer: Optional[str] = None
