from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models.batches import Batch, Batches
from tests.constants import BASE_URL, BATCH, BATCH_BY_ID_URL, BATCHES, BATCHES_LIST, BATCHES_URL


def test_create_batch(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=chat_completions", json=BATCH)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.create_batch(file='{"id":"1","request":{}}', method="chat_completions")

    assert isinstance(response, Batch)


def test_get_batches(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCH_BY_ID_URL, json=BATCHES)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.get_batches(batch_id="batch_1")

    assert isinstance(response, Batches)
    assert response.batches[0].id_ == "batch_1"


async def test_acreate_batch(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=embedder", json=BATCH)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.acreate_batch(file=b'{"id":"1","request":{}}', method="embedder")

    assert isinstance(response, Batch)


async def test_aget_batches(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCHES_URL, json=BATCHES_LIST)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_batches()

    assert isinstance(response, Batches)
    assert len(response.batches) == 1
