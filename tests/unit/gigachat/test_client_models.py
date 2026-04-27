import warnings

import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import Model, Models
from gigachat.resources.models import ModelsAsyncResource, ModelsSyncResource
from tests.constants import BASE_URL, MODEL, MODEL_URL, MODELS, MODELS_URL


def test_models_resource_is_cached_property() -> None:
    client = GigaChatSyncClient()

    assert "models" not in client.__dict__

    resource = client.models

    assert resource is client.models
    assert isinstance(resource, ModelsSyncResource)


async def test_a_models_resource_is_cached_property() -> None:
    client = GigaChatAsyncClient()

    assert "a_models" not in client.__dict__

    resource = client.a_models

    assert resource is client.a_models
    assert isinstance(resource, ModelsAsyncResource)


def test_models_list(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.models.list()

    assert isinstance(response, Models)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_models_retrieve(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.models.retrieve("model")

    assert isinstance(response, Model)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_get_models_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.models\.list\(\)"):
            response = client.get_models()

    assert isinstance(response, Models)


def test_get_model_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.models\.retrieve\(\.\.\.\)"):
            response = client.get_model("model")

    assert isinstance(response, Model)


async def test_a_models_list(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_models.list()

    assert isinstance(response, Models)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_a_models_retrieve(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_models.retrieve("model")

    assert isinstance(response, Model)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_aget_models_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_models\.list\(\)"):
            response = await client.aget_models()

    assert isinstance(response, Models)


async def test_aget_model_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_models\.retrieve\(\.\.\.\)"):
            response = await client.aget_model("model")

    assert isinstance(response, Model)
