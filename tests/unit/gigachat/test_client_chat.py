import warnings
from typing import Any, Optional, cast

import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from gigachat.api import legacy_chat
from gigachat.client import (
    GIGACHAT_MODEL,
    GigaChatAsyncClient,
    GigaChatSyncClient,
    _parse_chat,
)
from gigachat.exceptions import AuthenticationError
from gigachat.models import (
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
    Messages,
    MessagesRole,
)
from gigachat.settings import Settings
from tests.constants import (
    ACCESS_TOKEN,
    AUTH_URL,
    BASE_URL,
    CHAT,
    CHAT_COMPLETION,
    CHAT_COMPLETION_FUNCTION,
    CHAT_COMPLETION_STREAM,
    CHAT_FUNCTION,
    CHAT_URL,
    CREDENTIALS,
    HEADERS_STREAM,
    OAUTH_TOKEN_EXPIRED,
    OAUTH_TOKEN_VALID,
    PASSWORD,
    PASSWORD_TOKEN_EXPIRED,
    PASSWORD_TOKEN_VALID,
    TOKEN_URL,
    USER,
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
def test__parse_chat_model(payload_value: Optional[str], setting_value: Optional[str], expected: str) -> None:
    actual = _parse_chat(Chat(messages=[], model=payload_value), Settings(model=setting_value))
    assert actual.model is expected


@pytest.mark.parametrize(
    ("payload_value", "setting_value", "expected"),
    [
        (None, None, None),
        (None, False, False),
        (None, True, True),
        (False, None, False),
        (False, False, False),
        (False, True, False),
        (True, None, True),
        (True, False, True),
        (True, True, True),
    ],
)
def test__parse_chat_profanity_check(
    payload_value: Optional[bool],
    setting_value: Optional[bool],
    expected: Optional[bool],
) -> None:
    actual = _parse_chat(
        Chat(messages=[], profanity_check=payload_value),
        Settings(profanity_check=setting_value),
    )
    assert actual.profanity_check is expected


def test_chat(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.chat\(\.\.\.\)"):
            response = client.chat("text")

    assert isinstance(response, ChatCompletion)


def test_chat_rejects_pydantic_response_format_on_chat() -> None:
    class MathResult(BaseModel):
        answer: str

    payload = {
        "messages": [{"role": "user", "content": "Solve 2+2"}],
        "response_format": MathResult,
    }

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(TypeError, match="client\\.chat\\.legacy\\.parse"):
            client.chat.legacy.create(payload)


def test_chat_legacy_create_does_not_warn(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.chat.legacy.create("text")

    assert isinstance(response, ChatCompletion)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_chat_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = client.chat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = client.chat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_credentials_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused across multiple API calls (no duplicate auth requests)."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = client.chat.legacy.create(CHAT)
        response2 = client.chat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_credentials_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers new auth request for each API call."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = client.chat.legacy.create(CHAT)
        response2 = client.chat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_user_password_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused with user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = client.chat.legacy.create(CHAT)
        response2 = client.chat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_user_password_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers refresh with user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = client.chat.legacy.create(CHAT)
        response2 = client.chat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response = client.chat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            client.chat.legacy.create(CHAT)


def test_chat_update_token_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        access_token=ACCESS_TOKEN,
        credentials=CREDENTIALS,
    ) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat.legacy.create(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


def test_chat_update_token_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat.legacy.create(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


def test_chat_update_token_false(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat.legacy.create(CHAT)
        assert client.token == ACCESS_TOKEN


def test_chat_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        response = client.chat.legacy.create(CHAT)

    assert client.token
    assert client.token != ACCESS_TOKEN
    assert isinstance(response, ChatCompletion)


def test_chat_update_token_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat.legacy.create(CHAT)

    assert client.token
    assert client.token != ACCESS_TOKEN


def test_chat_with_functions(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION_FUNCTION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = client.chat.legacy.create(CHAT_FUNCTION)

    assert isinstance(response, ChatCompletion)
    assert response.choices[0].finish_reason == "function_call"
    assert response.choices[0].message.function_call is not None
    assert response.choices[0].message.function_call.name == "fc"
    assert response.choices[0].message.function_call.arguments is not None
    assert response.choices[0].message.function_call.arguments == {
        "location": "Москва",
        "num_days": 0,
    }


def test_stream_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.stream\(\.\.\.\)"):
            response = list(client.stream(CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_chat_legacy_stream_does_not_warn(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = list(client.chat.legacy.stream(CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_chat_legacy_create_uses_explicit_legacy_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_chat_sync(client: Any, *, chat: Chat, access_token: Optional[str] = None) -> ChatCompletion:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return ChatCompletion.model_validate(CHAT_COMPLETION)

    monkeypatch.setattr(legacy_chat, "chat_sync", fake_chat_sync)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = client.chat.legacy.create("text")

    assert isinstance(response, ChatCompletion)
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], Chat)


def test_chat_legacy_stream_uses_explicit_legacy_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_stream_sync(client: Any, *, chat: Chat, access_token: Optional[str] = None) -> Any:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return iter(
            [
                ChatCompletionChunk.model_validate(
                    {
                        "choices": [{"delta": {"content": "hello"}, "index": 0, "finish_reason": None}],
                        "created": 0,
                        "model": "test-model",
                        "object": "chat.completion.chunk",
                    }
                )
            ]
        )

    monkeypatch.setattr(legacy_chat, "stream_sync", fake_stream_sync)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = list(client.chat.legacy.stream("text"))

    assert len(response) == 1
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], Chat)


def test_stream_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            list(client.chat.legacy.stream(CHAT))


def test_stream_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        response = list(client.chat.legacy.stream(CHAT))

    assert client.token
    assert client.token != ACCESS_TOKEN
    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_stream_update_token_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            list(client.chat.legacy.stream(CHAT))

    assert client.token
    assert client.token != ACCESS_TOKEN


async def test_achat(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.achat\(\.\.\.\)"):
            response = await client.achat("text")

    assert isinstance(response, ChatCompletion)


async def test_achat_rejects_pydantic_response_format_on_chat() -> None:
    class MathResult(BaseModel):
        answer: str

    payload = Chat.model_construct(
        messages=[Messages(role=MessagesRole.USER, content="Solve 2+2")],
        response_format=cast(Any, MathResult),
    )

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(TypeError, match="client\\.chat\\.legacy\\.parse"):
            await client.achat.legacy.create(payload)


async def test_achat_legacy_create_does_not_warn(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.achat.legacy.create("text")

    assert isinstance(response, ChatCompletion)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_achat_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = await client.achat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


async def test_achat_legacy_create_uses_explicit_legacy_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    async def fake_chat_async(client: Any, *, chat: Chat, access_token: Optional[str] = None) -> ChatCompletion:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return ChatCompletion.model_validate(CHAT_COMPLETION)

    monkeypatch.setattr(legacy_chat, "chat_async", fake_chat_async)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = await client.achat.legacy.create("text")

    assert isinstance(response, ChatCompletion)
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], Chat)


async def test_achat_legacy_stream_uses_explicit_legacy_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    async def iterate() -> Any:
        yield ChatCompletionChunk.model_validate(
            {
                "choices": [{"delta": {"content": "hello"}, "index": 0, "finish_reason": None}],
                "created": 0,
                "model": "test-model",
                "object": "chat.completion.chunk",
            }
        )

    def fake_stream_async(client: Any, *, chat: Chat, access_token: Optional[str] = None) -> Any:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return iterate()

    monkeypatch.setattr(legacy_chat, "stream_async", fake_stream_async)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = [chunk async for chunk in client.achat.legacy.stream("text")]

    assert len(response) == 1
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], Chat)


async def test_achat_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = await client.achat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


async def test_achat_credentials_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused across multiple async API calls (no duplicate auth requests)."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = await client.achat.legacy.create(CHAT)
        response2 = await client.achat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_credentials_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers new auth request for each async API call."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = await client.achat.legacy.create(CHAT)
        response2 = await client.achat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_user_password_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused with async user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = await client.achat.legacy.create(CHAT)
        response2 = await client.achat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_user_password_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers refresh with async user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = await client.achat.legacy.create(CHAT)
        response2 = await client.achat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response = await client.achat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


async def test_achat_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            await client.achat.legacy.create(CHAT)


async def test_achat_update_token_false(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, access_token=ACCESS_TOKEN) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            await client.achat.legacy.create(CHAT)
        assert client.token == ACCESS_TOKEN


async def test_achat_update_token_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        access_token=ACCESS_TOKEN,
        credentials=CREDENTIALS,
    ) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            await client.achat.legacy.create(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


async def test_achat_update_token_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD
    ) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            await client.achat.legacy.create(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


async def test_astream_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD
    ) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.astream\(\.\.\.\)"):
            response = [chunk async for chunk in client.astream(CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


async def test_achat_legacy_stream_does_not_warn(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = [chunk async for chunk in client.achat.legacy.stream(CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_astream_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            _ = [chunk async for chunk in client.achat.legacy.stream(CHAT)]


async def test_astream_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD
    ) as client:
        assert client.token == ACCESS_TOKEN
        response = [chunk async for chunk in client.achat.legacy.stream(CHAT)]

    assert client.token
    assert client.token != ACCESS_TOKEN
    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


async def test_astream_update_token_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD
    ) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            _ = [chunk async for chunk in client.achat.legacy.stream(CHAT)]
        assert client.token
        assert client.token != ACCESS_TOKEN
