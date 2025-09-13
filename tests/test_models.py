from __future__ import annotations

from quorabroker.models import FetchRequest, ParsedPage


def test_fetch_request_valid(fetch_request: FetchRequest) -> None:
    assert fetch_request.url.host == "www.quora.com"  # type: ignore[attr-defined]


def test_parsed_page(parsed_page: ParsedPage) -> None:
    assert parsed_page.question == "Q?"
    assert parsed_page.answer == "A"
