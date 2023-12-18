from typing import Optional, List

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from gigachat.client import (
    GIGACHAT_MODEL,
    GigaChatAsyncClient,
    GigaChatSyncClient,
    _get_auth_kwargs,
    _get_kwargs,
    _logger,
    _parse_chat,
)
from gigachat.exceptions import AuthenticationError
from gigachat.models import Chat, ChatCompletion, ChatCompletionChunk, Model, Models, TokensCount
from gigachat.settings import Settings

from ...utils import get_bytes, get_json

BASE_URL = "http://base_url"
AUTH_URL = "http://auth_url"
CHAT_URL = f"{BASE_URL}/chat/completions"
TOKEN_URL = f"{BASE_URL}/token"
MODELS_URL = f"{BASE_URL}/models"
MODEL_URL = f"{BASE_URL}/models/model"
TOKENS_COUNT_URL = f"{BASE_URL}/tokens/count"

ACCESS_TOKEN = get_json("access_token.json")
TOKEN = get_json("token.json")
CHAT = Chat.parse_obj(get_json("chat.json"))
CHAT_COMPLETION = get_json("chat_completion.json")
CHAT_COMPLETION_STREAM = get_bytes("chat_completion.stream")
MODELS = get_json("models.json")
TOKENS_COUNT = get_json("tokens_count.json")
MODEL = get_json("model.json")

HEADERS_STREAM = {"Content-Type": "text/event-stream"}

CREDENTIALS = "NmIwNzhlODgtNDlkNC00ZjFmLTljMjMtYjFiZTZjMjVmNTRlOmU3NWJlNjVhLTk4YjAtNGY0Ni1iOWVhLTljMDkwZGE4YTk4MQ=="


def test__get_kwargs() -> None:
    settings = Settings(ca_bundle_file="ca.pem", cert_file="tls.pem", key_file="tls.key")
    assert _get_kwargs(settings)


def test__get_auth_kwargs() -> None:
    settings = Settings(ca_bundle_file="ca.pem", cert_file="tls.pem", key_file="tls.key")
    assert _get_auth_kwargs(settings)


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
    payload_value: Optional[bool], setting_value: Optional[bool], expected: Optional[bool]
) -> None:
    actual = _parse_chat(Chat(messages=[], profanity_check=payload_value), Settings(profanity_check=setting_value))
    assert actual.profanity_check is expected


def test__unknown_kwargs(mocker: MockerFixture) -> None:
    spy = mocker.spy(_logger, "warning")

    GigaChatSyncClient(foo="bar")

    assert spy.call_count == 1


def test_get_tokens_count(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.tokens_count(input=["123"], model="GigaChat:latest")
    assert isinstance(response, List)
    for row in response:
        assert isinstance(row, TokensCount)


def test_get_models(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.get_models()

    assert isinstance(response, Models)


def test_get_model(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.get_model("model")

    assert isinstance(response, Model)


def test_chat(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        response = client.chat("text")

    assert isinstance(response, ChatCompletion)


def test_chat_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token) as client:
        response = client.chat(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = client.chat(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)

    with GigaChatSyncClient(base_url=BASE_URL, user="user", password="password") as client:
        response = client.chat(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)


def test_chat_update_token_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    access_token = "access_token"

    with GigaChatSyncClient(
        base_url=BASE_URL, auth_url=AUTH_URL, access_token=access_token, credentials=CREDENTIALS
    ) as client:
        assert client.token == access_token
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)
        assert client.token
        assert client.token != access_token


def test_chat_update_token_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token, user="user", password="password") as client:
        assert client.token == access_token
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)
        assert client.token
        assert client.token != access_token


def test_chat_update_token_false(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token) as client:
        assert client.token == access_token
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)
        assert client.token == access_token


def test_chat_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token, user="user", password="password") as client:
        assert client.token == access_token
        response = client.chat(CHAT)

    assert client.token
    assert client.token != access_token
    assert isinstance(response, ChatCompletion)


def test_chat_update_token_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token, user="user", password="password") as client:
        assert client.token == access_token
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)

    assert client.token
    assert client.token != access_token


def test_stream(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = list(client.stream(CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_stream_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token, user="user", password="password") as client:
        response = list(client.stream(CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_stream_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            list(client.stream(CHAT))


def test_stream_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token, user="user", password="password") as client:
        assert client.token == access_token
        response = list(client.stream(CHAT))

    assert client.token
    assert client.token != access_token
    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_stream_update_token_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token, user="user", password="password") as client:
        assert client.token == access_token
        with pytest.raises(AuthenticationError):
            list(client.stream(CHAT))

    assert client.token
    assert client.token != access_token


@pytest.mark.asyncio()
async def test_aget_models(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_models()

    assert isinstance(response, Models)


@pytest.mark.asyncio()
async def test_atokens_count(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.atokens_count(input=["text"], model="GigaChat:latest")

    assert isinstance(response, List)
    for row in response:
        assert isinstance(row, TokensCount)


@pytest.mark.asyncio()
async def test_aget_model(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_model("model")

    assert isinstance(response, Model)


@pytest.mark.asyncio()
async def test_achat(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.achat("text")

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_achat_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    access_token = "access_token"

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=access_token) as client:
        response = await client.achat(CHAT)

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_achat_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = await client.achat(CHAT)

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_achat_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)

    async with GigaChatAsyncClient(base_url=BASE_URL, user="user", password="password") as client:
        response = await client.achat(CHAT)

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_achat_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            await client.achat(CHAT)


@pytest.mark.asyncio()
async def test_achat_update_token_false(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    access_token = "access_token"

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, access_token=access_token) as client:
        assert client.token == access_token
        with pytest.raises(AuthenticationError):
            await client.achat(CHAT)
        assert client.token == access_token


@pytest.mark.asyncio()
async def test_achat_update_token_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    access_token = "access_token"

    async with GigaChatAsyncClient(
        base_url=BASE_URL, auth_url=AUTH_URL, access_token=access_token, credentials=CREDENTIALS
    ) as client:
        assert client.token == access_token
        with pytest.raises(AuthenticationError):
            await client.achat(CHAT)
        assert client.token
        assert client.token != access_token


@pytest.mark.asyncio()
async def test_achat_update_token_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    access_token = "access_token"

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=access_token, user="user", password="password"
    ) as client:
        assert client.token == access_token
        with pytest.raises(AuthenticationError):
            await client.achat(CHAT)
        assert client.token
        assert client.token != access_token


@pytest.mark.asyncio()
async def test_astream(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = [chunk async for chunk in client.astream(CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


@pytest.mark.asyncio()
async def test_astream_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    access_token = "access_token"

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=access_token, user="user", password="password"
    ) as client:
        response = [chunk async for chunk in client.astream(CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


@pytest.mark.asyncio()
async def test_astream_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            _ = [chunk async for chunk in client.astream(CHAT)]


@pytest.mark.asyncio()
async def test_astream_update_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    access_token = "access_token"

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=access_token, user="user", password="password"
    ) as client:
        assert client.token == access_token
        with pytest.raises(AuthenticationError):
            _ = [chunk async for chunk in client.astream(CHAT)]
        assert client.token
        assert client.token != access_token


def test__update_token() -> None:
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        client._update_token()


@pytest.mark.asyncio()
async def test__aupdate_token() -> None:
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        await client._aupdate_token()
