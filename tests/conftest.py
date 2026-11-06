"""Shared HTTPX2 test fixtures."""

from collections.abc import Generator

import pytest

from tests.httpx_mock import HTTPXMock, install_mock


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--record-mode", choices=["none"], default="none", help="Replay checked-in cassettes; network is disabled"
    )


@pytest.fixture
def httpx_mock(monkeypatch: pytest.MonkeyPatch) -> Generator[HTTPXMock, None, None]:
    mock = HTTPXMock()
    install_mock(monkeypatch, mock)
    yield mock
    mock.assert_all_responses_requested()
