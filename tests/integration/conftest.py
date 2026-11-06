"""Replay existing cassettes with native HTTPX2 and no live network access."""

import os
import socket
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import pytest

from gigachat import GigaChat
from tests.httpx_mock import CassetteReplay, install_mock

CASSETTE_BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
CASSETTE_MODEL = "GigaChat"


@pytest.fixture(autouse=True)
def cassette_replay(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Generator[CassetteReplay, None, None]:
    """Replay only recorded requests and block socket creation for every integration test."""

    def reject_network(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Live network access is disabled during cassette replay")

    monkeypatch.setattr(socket.socket, "connect", reject_network)
    monkeypatch.setattr(socket.socket, "connect_ex", reject_network)
    path = Path(__file__).parent / "cassettes" / f"{request.node.originalname}.yaml"
    replay = CassetteReplay(path)
    install_mock(monkeypatch, replay)
    # Example imports during full test collection may load .env. Authentication
    # replay always uses dummy OAuth settings and must not inherit those values.
    for name in list(os.environ):
        if name.startswith("GIGACHAT_"):
            monkeypatch.delenv(name)
    yield replay
    replay.assert_all_responses_requested()


def _client_settings() -> dict[str, Any]:
    return {
        "base_url": CASSETTE_BASE_URL,
        "model": CASSETTE_MODEL,
        "credentials": "ZHVtbXktY2xpZW50OmR1bW15LXNlY3JldA==",
        "scope": "GIGACHAT_API_PERS",
        "verify_ssl_certs": False,
        "timeout": 120,
    }


@pytest.fixture
def gigachat_client(cassette_replay: CassetteReplay) -> Generator[GigaChat, None, None]:
    with GigaChat(**_client_settings()) as client:
        yield client


@pytest.fixture
async def gigachat_async_client(cassette_replay: CassetteReplay) -> AsyncGenerator[GigaChat, None]:
    async with GigaChat(**_client_settings()) as client:
        yield client
