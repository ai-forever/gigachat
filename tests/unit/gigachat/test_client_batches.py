import warnings

import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import Batch, Batches
from gigachat.resources.batches import BatchesAsyncResource, BatchesSyncResource
from tests.constants import BASE_URL, BATCH, BATCH_BY_ID_URL, BATCHES, BATCHES_URL


def test_batches_resource_is_cached_property() -> None:
    client = GigaChatSyncClient()

    assert "batches" not in client.__dict__

    resource = client.batches

    assert resource is client.batches
    assert isinstance(resource, BatchesSyncResource)


async def test_a_batches_resource_is_cached_property() -> None:
    client = GigaChatAsyncClient()

    assert "a_batches" not in client.__dict__

    resource = client.a_batches

    assert resource is client.a_batches
    assert isinstance(resource, BatchesAsyncResource)


def test_batches_create(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=chat_completions", json=BATCH)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.batches.create('{"id":"1","request":{}}', method="chat_completions")

    assert isinstance(response, Batch)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_batches_list(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCHES_URL, json=BATCHES)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.batches.list()

    assert isinstance(response, Batches)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_batches_retrieve(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCH_BY_ID_URL, json=BATCH)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.batches.retrieve("batch_1")

    assert isinstance(response, Batches)
    assert response.batches[0].id_ == "batch_1"
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_create_batch_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=chat_completions", json=BATCH)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.batches\.create\(\.\.\.\)"):
            response = client.create_batch('{"id":"1","request":{}}', method="chat_completions")

    assert isinstance(response, Batch)


def test_get_batches_deprecated_shim_list(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCHES_URL, json=BATCHES)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.batches\.list\(\)"):
            response = client.get_batches()

    assert isinstance(response, Batches)


def test_get_batches_deprecated_shim_retrieve(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCH_BY_ID_URL, json=BATCH)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.batches\.retrieve\(\.\.\.\)"):
            response = client.get_batches(batch_id="batch_1")

    assert isinstance(response, Batches)
    assert response.batches[0].id_ == "batch_1"


async def test_a_batches_create(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=embedder", json=BATCH)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_batches.create(b'{"id":"1","request":{}}', method="embedder")

    assert isinstance(response, Batch)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_a_batches_list(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCHES_URL, json=BATCHES)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_batches.list()

    assert isinstance(response, Batches)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_a_batches_retrieve(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCH_BY_ID_URL, json=BATCH)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_batches.retrieve("batch_1")

    assert isinstance(response, Batches)
    assert response.batches[0].id_ == "batch_1"
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_acreate_batch_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=chat_completions", json=BATCH)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_batches\.create\(\.\.\.\)"):
            response = await client.acreate_batch('{"id":"1","request":{}}', method="chat_completions")

    assert isinstance(response, Batch)


async def test_aget_batches_deprecated_shim_list(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCHES_URL, json=BATCHES)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_batches\.list\(\)"):
            response = await client.aget_batches()

    assert isinstance(response, Batches)


async def test_aget_batches_deprecated_shim_retrieve(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCH_BY_ID_URL, json=BATCH)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_batches\.retrieve\(\.\.\.\)"):
            response = await client.aget_batches(batch_id="batch_1")

    assert isinstance(response, Batches)
    assert response.batches[0].id_ == "batch_1"
