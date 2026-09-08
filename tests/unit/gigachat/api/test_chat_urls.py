from typing import List, Tuple

import httpx
import pytest

from gigachat.api import chat as legacy_chat
from gigachat.api import chat_completions as primary_chat
from gigachat.api.utils import resolve_legacy_chat_url, resolve_primary_chat_url
from gigachat.models.chat import Chat
from gigachat.models.chat_completions import ChatCompletionRequest, ChatMessage

LEGACY_CASES: List[Tuple[str, str]] = [
    ("https://api.giga.chat", "https://api.giga.chat/v1/chat/completions"),
    ("https://api.gigachat.ru", "https://api.gigachat.ru/v1/chat/completions"),
    ("https://api.giga.chat/v1", "https://api.giga.chat/v1/chat/completions"),
    ("https://api.giga.chat/api/v1", "https://api.giga.chat/api/v1/chat/completions"),
    ("https://proxy.example", "https://proxy.example/chat/completions"),
    ("https://proxy.example/gateway", "https://proxy.example/gateway/chat/completions"),
]

PRIMARY_CASES: List[Tuple[str, str]] = [
    ("https://api.giga.chat", "https://api.giga.chat/v2/chat/completions"),
    ("https://api.gigachat.ru", "https://api.gigachat.ru/v2/chat/completions"),
    ("https://api.giga.chat/v1", "https://api.giga.chat/v2/chat/completions"),
    ("https://api.giga.chat/api/v1", "https://api.giga.chat/api/v2/chat/completions"),
    ("https://proxy.example", "https://proxy.example/chat/completions"),
    ("https://proxy.example/gateway", "https://proxy.example/gateway/chat/completions"),
]


@pytest.mark.parametrize(("base_url", "expected_url"), LEGACY_CASES)
def test_resolve_legacy_chat_url_sync(base_url: str, expected_url: str) -> None:
    with httpx.Client(base_url=base_url) as client:
        url = resolve_legacy_chat_url(client, "/chat/completions")
        request = client.build_request("POST", url)

    assert str(request.url) == expected_url


@pytest.mark.parametrize(("base_url", "expected_url"), LEGACY_CASES)
async def test_resolve_legacy_chat_url_async(base_url: str, expected_url: str) -> None:
    async with httpx.AsyncClient(base_url=base_url) as client:
        url = resolve_legacy_chat_url(client, "/chat/completions")
        request = client.build_request("POST", url)

    assert str(request.url) == expected_url


@pytest.mark.parametrize(("base_url", "expected_url"), PRIMARY_CASES)
def test_resolve_primary_chat_url_sync(base_url: str, expected_url: str) -> None:
    with httpx.Client(base_url=base_url) as client:
        url = resolve_primary_chat_url(client, None)
        request = client.build_request("POST", url)

    assert str(request.url) == expected_url


@pytest.mark.parametrize(("base_url", "expected_url"), PRIMARY_CASES)
async def test_resolve_primary_chat_url_async(base_url: str, expected_url: str) -> None:
    async with httpx.AsyncClient(base_url=base_url) as client:
        url = resolve_primary_chat_url(client, None)
        request = client.build_request("POST", url)

    assert str(request.url) == expected_url


def test_chat_url_resolvers_preserve_explicit_overrides() -> None:
    with httpx.Client(base_url="https://api.giga.chat/api/v1") as client:
        legacy_url = resolve_legacy_chat_url(client, "https://proxy.example/custom/chat")
        primary_url = resolve_primary_chat_url(client, "/v2/custom/chat")

    assert legacy_url == "https://proxy.example/custom/chat"
    assert primary_url == "https://api.giga.chat/v2/custom/chat"


@pytest.mark.parametrize("host", ["api.giga.chat", "api.gigachat.ru"])
def test_sync_chat_and_stream_builders_use_documented_versioned_routes(host: str) -> None:
    legacy_request = Chat(messages=[])
    primary_request = ChatCompletionRequest(messages=[ChatMessage(role="user", content="Привет")])

    with httpx.Client(base_url=f"https://{host}") as client:
        legacy_url = f"https://{host}/v1/chat/completions"
        primary_url = f"https://{host}/v2/chat/completions"
        assert legacy_chat._get_chat_kwargs(client, chat=legacy_request)["url"] == legacy_url
        assert legacy_chat._get_stream_kwargs(client, chat=legacy_request)["url"] == legacy_url
        assert primary_chat._get_chat_kwargs(client, chat=primary_request)["url"] == primary_url
        assert primary_chat._get_stream_kwargs(client, chat=primary_request)["url"] == primary_url


@pytest.mark.parametrize("host", ["api.giga.chat", "api.gigachat.ru"])
async def test_async_chat_and_stream_builders_use_documented_versioned_routes(host: str) -> None:
    legacy_request = Chat(messages=[])
    primary_request = ChatCompletionRequest(messages=[ChatMessage(role="user", content="Привет")])

    async with httpx.AsyncClient(base_url=f"https://{host}") as client:
        legacy_url = f"https://{host}/v1/chat/completions"
        primary_url = f"https://{host}/v2/chat/completions"
        assert legacy_chat._get_chat_kwargs(client, chat=legacy_request)["url"] == legacy_url
        assert legacy_chat._get_stream_kwargs(client, chat=legacy_request)["url"] == legacy_url
        assert primary_chat._get_chat_kwargs(client, chat=primary_request)["url"] == primary_url
        assert primary_chat._get_stream_kwargs(client, chat=primary_request)["url"] == primary_url
