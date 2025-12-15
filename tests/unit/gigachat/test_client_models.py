from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import Model, Models
from tests.constants import BASE_URL, MODEL, MODEL_URL, MODELS, MODELS_URL


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


async def test_aget_models(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_models()

    assert isinstance(response, Models)


async def test_aget_model(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_model("model")

    assert isinstance(response, Model)
