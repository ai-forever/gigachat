import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import post_token
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Token

from ....utils import get_json

BASE_URL = "http://testserver/api"
MOCK_URL = f"{BASE_URL}/token"

TOKEN = get_json("token.json")


def test_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=TOKEN)

    with httpx.Client(base_url=BASE_URL) as client:
        response = post_token.sync(client, user="user", password="password")

    assert isinstance(response, Token)


def test_sync_value_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json={})

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="2 validation errors for Token*"):
            post_token.sync(client, user="user", password="password")


def test_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            post_token.sync(client, user="user", password="password")


def test_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ResponseError):
            post_token.sync(client, user="user", password="password")


def test_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=TOKEN)

    with httpx.Client(base_url=BASE_URL) as client:
        response = post_token.sync(
            client,
            user="user",
            password="password",
        )

    assert isinstance(response, Token)


@pytest.mark.asyncio()
async def test_asyncio(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MOCK_URL, json=TOKEN)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await post_token.asyncio(client, user="user", password="password")

    assert isinstance(response, Token)
