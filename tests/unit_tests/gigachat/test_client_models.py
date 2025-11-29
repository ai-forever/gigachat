import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import Model, Models

from ...utils import get_json

BASE_URL = "http://base_url"
MODELS_URL = f"{BASE_URL}/models"
MODEL_URL = f"{BASE_URL}/models/model"

MODELS = get_json("models.json")
MODEL = get_json("model.json")


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


@pytest.mark.asyncio
async def test_aget_models(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_models()

    assert isinstance(response, Models)


@pytest.mark.asyncio
async def test_aget_model(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_model("model")

    assert isinstance(response, Model)
