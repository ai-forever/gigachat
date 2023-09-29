import httpx
import pytest

from gigachat.api import post_chat
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Chat, ChatCompletion

from ....utils import get_json

BASE_URL = "http://testserver/api"
MOCK_URL = f"{BASE_URL}/chat/completions"

CHAT = Chat.parse_obj(get_json("chat.json"))
CHAT_COMPLETION = get_json("chat_completion.json")


def test_sync(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    with httpx.Client(base_url=BASE_URL) as client:
        response = post_chat.sync(client, chat=CHAT)

    assert isinstance(response, ChatCompletion)


def test_sync_value_error(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, json={})

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="5 validation errors for ChatCompletion*"):
            post_chat.sync(client, chat=CHAT)


def test_sync_authentication_error(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            post_chat.sync(client, chat=CHAT)


def test_sync_response_error(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ResponseError):
            post_chat.sync(client, chat=CHAT)


def test_sync_headers(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    with httpx.Client(base_url=BASE_URL) as client:
        response = post_chat.sync(
            client,
            chat=CHAT,
            access_token="access_token",
            client_id="client_id",
            session_id="session_id",
            request_id="request_id",
        )

    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio()
async def test_asyncio(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, json=CHAT_COMPLETION)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await post_chat.asyncio(client, chat=CHAT)

    assert isinstance(response, ChatCompletion)
