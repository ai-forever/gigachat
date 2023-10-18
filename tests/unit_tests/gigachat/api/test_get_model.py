import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import get_model
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Model

from ....utils import get_json

BASE_URL = "http://testserver/api"
MODEL_URL = f"{BASE_URL}/models/model"

MODEL = get_json("model.json")


def test_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_model.sync(client, model="model")

    assert isinstance(response, Model)


def test_sync_value_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json={})

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="3 validation errors for Model*"):
            get_model.sync(client, model="model")


def test_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            get_model.sync(client, model="model")


def test_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ResponseError):
            get_model.sync(client, model="model")


def test_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_model.sync(
            client,
            model="model",
            access_token="access_token",
            client_id="client_id",
            session_id="session_id",
            request_id="request_id",
        )

    assert isinstance(response, Model)


@pytest.mark.asyncio()
async def test_asyncio(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_model.asyncio(client, model="model")

    assert isinstance(response, Model)
