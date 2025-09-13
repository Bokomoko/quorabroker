from __future__ import annotations

from quorabroker.config import Settings


def test_settings_load(settings: Settings) -> None:
    assert isinstance(settings.kafka_bootstrap_servers, str)
    assert settings.request_topic
    assert settings.parsed_topic
