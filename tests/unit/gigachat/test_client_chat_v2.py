from typing import Optional

import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from gigachat.client import (
    GIGACHAT_MODEL,
    GigaChatAsyncClient,
    GigaChatSyncClient,
    _parse_chat_v2,
)
from gigachat.models.chat_v2 import ChatV2
from gigachat.settings import Settings
from tests.constants import (
    ACCESS_TOKEN,
    AUTH_URL,
    CHAT_COMPLETION_V2,
    CHAT_COMPLETION_V2_STREAM,
    CHAT_V2,
    CHAT_V2_BASE_URL,
    CHAT_V2_URL,
    CREDENTIALS,
    HEADERS_STREAM,
    OAUTH_TOKEN_VALID,
)


@pytest.mark.parametrize(
    ("payload_value", "setting_value", "expected"),
    [
        (None, None, GIGACHAT_MODEL),
        (None, "setting_model", "setting_model"),
        ("payload_model", None, "payload_model"),
        ("payload_model", "setting_model", "payload_model"),
    ],
)
def test__parse_chat_v2_model(payload_value: Optional[str], setting_value: Optional[str], expected: str) -> None:
    actual = _parse_chat_v2(
        ChatV2(messages=[{"role": "user", "content": "hi"}], model=payload_value),
        Settings(model=setting_value),
    )
    assert actual.model == expected


def test__parse_chat_v2_skips_model_default_for_assistant_or_thread() -> None:
    with_assistant = _parse_chat_v2(
        ChatV2(messages=[{"role": "user", "content": "hi"}], assistant_id="assistant-1"),
        Settings(model="setting-model"),
    )
    with_thread = _parse_chat_v2(
        ChatV2(messages=[{"role": "user", "content": "hi"}], storage={"thread_id": "thread-1"}),
        Settings(model="setting-model"),
    )

    assert with_assistant.model is None
    assert with_thread.model is None


def test__parse_chat_v2_from_string_and_flags() -> None:
    actual = _parse_chat_v2("text", Settings(flags=["preprocess"]))

    assert actual.messages[0].role == "user"
    assert actual.messages[0].content[0].text == "text"
    assert actual.flags == ["preprocess"]


def test__parse_chat_v2_accepts_tool_string_shorthand() -> None:
    actual = _parse_chat_v2(
        {"messages": [{"role": "user", "content": "hi"}], "tools": ["web_search"]},
        Settings(),
    )

    assert actual.tools is not None
    assert actual.tools[0].model_dump(exclude_none=True) == {"web_search": {}}


def test_chat_v2(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, json=CHAT_COMPLETION_V2)

    with GigaChatSyncClient(base_url=CHAT_V2_BASE_URL, model="model") as client:
        response = client.chat_v2("text")

    assert response.model == "GigaChat-2-Max"
    request = httpx_mock.get_requests()[0]
    assert str(request.url) == CHAT_V2_URL


def test_chat_v2_rejects_pydantic_response_format_on_direct_request() -> None:
    class MathResult(BaseModel):
        answer: str

    payload = {
        "messages": [{"role": "user", "content": "Solve 2+2"}],
        "model_options": {"response_format": MathResult},
    }

    with GigaChatSyncClient(base_url=CHAT_V2_BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(TypeError, match="use `client.chat_parse_v2\\(payload, response_format=.*instead"):
            client.chat_v2(payload)


def test_chat_v2_with_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_V2_URL, json=CHAT_COMPLETION_V2)

    with GigaChatSyncClient(base_url=CHAT_V2_BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = client.chat_v2(CHAT_V2)

    assert response.messages[0].role == "assistant"


def test_stream_v2(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, content=CHAT_COMPLETION_V2_STREAM, headers=HEADERS_STREAM)

    with GigaChatSyncClient(base_url=CHAT_V2_BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = list(client.stream_v2(CHAT_V2))

    assert len(response) == 2
    assert response[0].event == "response.message.delta"
    assert response[1].event == "response.message.done"
    assert response[1].messages is None
    assert response[1].finish_reason == "stop"


def test_chat_v2_invalid_default_base_url() -> None:
    with GigaChatSyncClient(base_url="http://base_url", access_token=ACCESS_TOKEN) as client:
        with pytest.raises(ValueError, match="Cannot derive v2 chat URL"):
            client.chat_v2("text")


async def test_achat_v2(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, json=CHAT_COMPLETION_V2)

    async with GigaChatAsyncClient(base_url=CHAT_V2_BASE_URL, model="model") as client:
        response = await client.achat_v2("text")

    assert response.model == "GigaChat-2-Max"


async def test_achat_v2_rejects_pydantic_response_format_on_direct_request() -> None:
    class MathResult(BaseModel):
        answer: str

    payload = {
        "messages": [{"role": "user", "content": "Solve 2+2"}],
        "model_options": {"response_format": MathResult},
    }

    async with GigaChatAsyncClient(base_url=CHAT_V2_BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(TypeError, match="use `client.chat_parse_v2\\(payload, response_format=.*instead"):
            await client.achat_v2(payload)


async def test_astream_v2(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, content=CHAT_COMPLETION_V2_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(base_url=CHAT_V2_BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = [chunk async for chunk in client.astream_v2(CHAT_V2)]

    assert len(response) == 2
    assert response[0].event == "response.message.delta"
    assert response[1].event == "response.message.done"
    assert response[0].messages[0].role == "assistant"
    assert response[1].messages is None
