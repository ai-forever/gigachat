from typing import Any, Optional, cast

import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

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
        with pytest.raises(TypeError, match="use `client.chat_parse\\(payload, response_format=.*instead"):
            client.chat(payload)


def test_chat_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = client.chat(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = client.chat(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_credentials_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused across multiple API calls (no duplicate auth requests)."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = client.chat(CHAT)
        response2 = client.chat(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_credentials_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers new auth request for each API call."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = client.chat(CHAT)
        response2 = client.chat(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_user_password_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused with user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = client.chat(CHAT)
        response2 = client.chat(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_user_password_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers refresh with user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = client.chat(CHAT)
        response2 = client.chat(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response = client.chat(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)


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
            client.chat(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


def test_chat_update_token_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


def test_chat_update_token_false(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)
        assert client.token == ACCESS_TOKEN


def test_chat_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        response = client.chat(CHAT)

    assert client.token
    assert client.token != ACCESS_TOKEN
    assert isinstance(response, ChatCompletion)


def test_chat_update_token_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)

    assert client.token
    assert client.token != ACCESS_TOKEN


def test_chat_with_functions(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION_FUNCTION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = client.chat(CHAT_FUNCTION)

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
        response = list(client.stream(CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_stream_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            list(client.stream(CHAT))


def test_stream_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        response = list(client.stream(CHAT))

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
            list(client.stream(CHAT))

    assert client.token
    assert client.token != ACCESS_TOKEN


async def test_achat(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
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
        with pytest.raises(TypeError, match="use `client.chat_parse\\(payload, response_format=.*instead"):
            await client.achat(payload)


async def test_achat_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = await client.achat(CHAT)

    assert isinstance(response, ChatCompletion)


async def test_achat_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = await client.achat(CHAT)

    assert isinstance(response, ChatCompletion)


async def test_achat_credentials_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused across multiple async API calls (no duplicate auth requests)."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = await client.achat(CHAT)
        response2 = await client.achat(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_credentials_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers new auth request for each async API call."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = await client.achat(CHAT)
        response2 = await client.achat(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_user_password_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused with async user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = await client.achat(CHAT)
        response2 = await client.achat(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_user_password_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers refresh with async user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = await client.achat(CHAT)
        response2 = await client.achat(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response = await client.achat(CHAT)

    assert isinstance(response, ChatCompletion)


async def test_achat_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            await client.achat(CHAT)


async def test_achat_update_token_false(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, access_token=ACCESS_TOKEN) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            await client.achat(CHAT)
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
            await client.achat(CHAT)
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
            await client.achat(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


async def test_astream_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD
    ) as client:
        response = [chunk async for chunk in client.astream(CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


async def test_astream_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            _ = [chunk async for chunk in client.astream(CHAT)]


async def test_astream_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD
    ) as client:
        assert client.token == ACCESS_TOKEN
        response = [chunk async for chunk in client.astream(CHAT)]

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
            _ = [chunk async for chunk in client.astream(CHAT)]
        assert client.token
        assert client.token != ACCESS_TOKEN
