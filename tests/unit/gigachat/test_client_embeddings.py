import json
import warnings

import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import Embeddings
from gigachat.resources.embeddings import EmbeddingsAsyncResource, EmbeddingsSyncResource
from tests.constants import BASE_URL, EMBEDDINGS, EMBEDDINGS_URL


def test_embeddings_resource_is_cached_property() -> None:
    client = GigaChatSyncClient()

    assert "embeddings" not in client.__dict__

    resource = client.embeddings

    assert resource is client.embeddings
    assert isinstance(resource, EmbeddingsSyncResource)


async def test_a_embeddings_resource_is_cached_property() -> None:
    client = GigaChatAsyncClient()

    assert "a_embeddings" not in client.__dict__

    resource = client.a_embeddings

    assert resource is client.a_embeddings
    assert isinstance(resource, EmbeddingsAsyncResource)


def test_embeddings_create(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.embeddings.create(["text"], model="model")

    assert isinstance(response, Embeddings)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_embeddings_create_uses_default_model(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.embeddings.create(["text"])

    request_body = json.loads(httpx_mock.get_requests()[0].content)

    assert isinstance(response, Embeddings)
    assert request_body == {"input": ["text"], "model": "Embeddings"}


def test_embeddings_callable_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.embeddings\.create\(\.\.\.\)"):
            response = client.embeddings(["text"], model="model")

    assert isinstance(response, Embeddings)


async def test_a_embeddings_create(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_embeddings.create(["text"], model="model")

    assert isinstance(response, Embeddings)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_a_embeddings_create_uses_default_model(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_embeddings.create(["text"])

    request_body = json.loads(httpx_mock.get_requests()[0].content)

    assert isinstance(response, Embeddings)
    assert request_body == {"input": ["text"], "model": "Embeddings"}


async def test_aembeddings_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_embeddings\.create\(\.\.\.\)"):
            response = await client.aembeddings(["text"], model="model")

    assert isinstance(response, Embeddings)
