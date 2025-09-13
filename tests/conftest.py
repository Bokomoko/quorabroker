"""Pytest fixtures for quorabroker.

Fixtures are focused on pure units (parser, models, config) until
service layers are implemented.
"""
from __future__ import annotations

import pytest
from quorabroker.config import Settings
from quorabroker.models import FetchRequest, ParsedPage


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.load()


@pytest.fixture
def sample_html() -> str:
    return """
    <html><head><title>Example</title></head>
    <body>
      <div class="puppeteer_test_question_title">What is Python?</div>
      <p class="q-text qu-display--block qu-wordBreak--break-word qu-textAlign--start">Python is a programming language.</p>
    </body>
    </html>
    """.strip()


@pytest.fixture
def fetch_request() -> FetchRequest:
    return FetchRequest(url="https://www.quora.com/What-is-Python")


@pytest.fixture
def parsed_page() -> ParsedPage:
    return ParsedPage(url="https://www.quora.com/What-is-Python", question="Q?", answer="A")
