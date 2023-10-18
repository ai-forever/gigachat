import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import get_models
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Models

from ....utils import get_json

BASE_URL = "http://testserver/api"
MODELS_URL = f"{BASE_URL}/models"

MODELS = get_json("models.json")


def test_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_models.sync(client)

    assert isinstance(response, Models)


def test_sync_value_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json={})

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="2 validation errors for Models*"):
            get_models.sync(client)


def test_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            get_models.sync(client)


def test_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ResponseError):
            get_models.sync(client)


def test_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_models.sync(
            client, access_token="access_token", client_id="client_id", session_id="session_id", request_id="request_id"
        )

    assert isinstance(response, Models)


@pytest.mark.asyncio()
async def test_asyncio(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_models.asyncio(client)

    assert isinstance(response, Models)
