"""Domain message models used across services."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, HttpUrl, Field


class FetchRequest(BaseModel):  # type: ignore[misc]
    url: HttpUrl
    id: Optional[str] = Field(default=None)


class ParsedPage(BaseModel):  # type: ignore[misc]
    url: HttpUrl
    id: Optional[str] = Field(default=None)
    question: Optional[str] = None
    answer: Optional[str] = None
