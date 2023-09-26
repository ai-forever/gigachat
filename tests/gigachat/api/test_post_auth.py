import httpx
import pytest

from gigachat.api import post_auth
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import AccessToken

from ...utils import get_resource

MOCK_URL = "http://testserver/foo"

ACCESS_TOKEN = get_resource("access_token.json")


def test_sync(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, json=ACCESS_TOKEN)

    with httpx.Client() as client:
        response = post_auth.sync(client, MOCK_URL, "credentials", "scope")

    assert isinstance(response, AccessToken)


def test_sync_value_error(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, json={})

    with httpx.Client() as client:
        with pytest.raises(ValueError, match="2 validation errors for AccessToken*"):
            post_auth.sync(client, MOCK_URL, "credentials", "scope")


def test_sync_authentication_error(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, status_code=401)

    with httpx.Client() as client:
        with pytest.raises(AuthenticationError):
            post_auth.sync(client, MOCK_URL, "credentials", "scope")


def test_sync_response_error(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, status_code=400)

    with httpx.Client() as client:
        with pytest.raises(ResponseError):
            post_auth.sync(client, MOCK_URL, "credentials", "scope")


@pytest.mark.asyncio()
async def test_asyncio(httpx_mock):
    httpx_mock.add_response(url=MOCK_URL, json=ACCESS_TOKEN)

    async with httpx.AsyncClient() as client:
        response = await post_auth.asyncio(client, MOCK_URL, "credentials", "scope")

    assert isinstance(response, AccessToken)
