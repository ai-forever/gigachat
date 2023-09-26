import pytest

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient, _get_client_id
from gigachat.exceptions import AuthenticationError
from gigachat.models import Chat, ChatCompletion, ChatCompletionChunk

from ..utils import get_content, get_resource

BASE_URL = "http://base_url"
AUTH_URL = "http://auth_url"
CHAT_URL = f"{BASE_URL}/chat/completions"
TOKEN_URL = f"{BASE_URL}/token"

ACCESS_TOKEN = get_resource("access_token.json")
TOKEN = get_resource("token.json")
CHAT = Chat.parse_obj(get_resource("chat.json"))
CHAT_COMPLETION = get_resource("chat_completion.json")
CHAT_COMPLETION_STREAM = get_content("chat_completion.stream")

HEADERS_STREAM = {"Content-Type": "text/event-stream"}

CREDENTIALS = "NmIwNzhlODgtNDlkNC00ZjFmLTljMjMtYjFiZTZjMjVmNTRlOmU3NWJlNjVhLTk4YjAtNGY0Ni1iOWVhLTljMDkwZGE4YTk4MQ=="
CLIENT_ID = "6b078e88-49d4-4f1f-9c23-b1be6c25f54e"


def test_get_client_id():
    assert _get_client_id(CREDENTIALS) == CLIENT_ID
    assert _get_client_id("") is None
    assert _get_client_id(None) is None


def test_chat(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, use_auth=False, model="model") as client:
        response = client.chat(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_access_token(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token) as client:
        response = client.chat(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_credentials(httpx_mock):
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = client.chat(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_user_password(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)

    with GigaChatSyncClient(base_url=BASE_URL, user="user", password="password") as client:
        response = client.chat(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_authentication_error(httpx_mock):
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)


def test_chat_update_token_credentials(httpx_mock):
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


def test_chat_update_token_user_password(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token, user="user", password="password") as client:
        assert client.token == access_token
        with pytest.raises(AuthenticationError):
            client.chat(CHAT)
        assert client.token
        assert client.token != access_token


def test_stream(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with GigaChatSyncClient(base_url=BASE_URL, use_auth=False) as client:
        response = list(client.stream(CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_stream_access_token(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    access_token = "access_token"

    with GigaChatSyncClient(base_url=BASE_URL, access_token=access_token) as client:
        response = list(client.stream(CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_stream_authentication_error(httpx_mock):
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            list(client.stream(CHAT))


def test_stream_update_token(httpx_mock):
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
async def test_achat(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, use_auth=False) as client:
        response = await client.achat(CHAT)

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_achat_access_token(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    access_token = "access_token"

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=access_token) as client:
        response = await client.achat(CHAT)

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_achat_credentials(httpx_mock):
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = await client.achat(CHAT)

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_achat_user_password(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=TOKEN)

    async with GigaChatAsyncClient(base_url=BASE_URL, user="user", password="password") as client:
        response = await client.achat(CHAT)

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_achat_authentication_error(httpx_mock):
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            await client.achat(CHAT)


@pytest.mark.asyncio()
async def test_achat_update_token_credentials(httpx_mock):
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
async def test_achat_update_token_user_password(httpx_mock):
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
async def test_astream(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(base_url=BASE_URL, use_auth=False) as client:
        response = [chunk async for chunk in client.astream(CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


@pytest.mark.asyncio()
async def test_astream_access_token(httpx_mock):
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)
    access_token = "access_token"

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=access_token) as client:
        response = [chunk async for chunk in client.astream(CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


@pytest.mark.asyncio()
async def test_astream_authentication_error(httpx_mock):
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            _ = [chunk async for chunk in client.astream(CHAT)]


@pytest.mark.asyncio()
async def test_astream_update_token(httpx_mock):
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


# if __name__ == '__main__':
#     payload = {
#         "messages": [
#             {"role": "system", "content": "Ты - умный ИИ ассистент, который всегда готов помочь пользователю."},
#             {"role": "assistant", "content": "Как я могу помочь вам?"},
#             {"role": "user", "content": "Привет!"},
#         ],
#         "profanity_check": False,
#         "temperature": 0.87,
#         "max_tokens": 512,
#     }
#
#     with GigaChatSyncClient(base_url="https://beta.saluteai.sberdevices.ru/v1") as giga:
#         response = giga.chat(payload)
#         print(response.dict())
