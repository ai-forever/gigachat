import httpx
from pytest_httpx import HTTPXMock

from gigachat.api.batches import create_batch_async, create_batch_sync, get_batches_async, get_batches_sync
from gigachat.models.batches import Batch, Batches
from tests.constants import BASE_URL, BATCH, BATCH_BY_ID_URL, BATCHES, BATCHES_LIST, BATCHES_URL


def test_create_batch_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=chat_completions", json=BATCH)

    with httpx.Client(base_url=BASE_URL) as client:
        response = create_batch_sync(client, file='{"id":"1","request":{}}', method="chat_completions")

    assert isinstance(response, Batch)


async def test_create_batch_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=embedder", json=BATCH)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await create_batch_async(client, file=b'{"id":"1","request":{}}', method="embedder")

    assert isinstance(response, Batch)


def test_get_batches_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCHES_URL, json=BATCHES_LIST)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_batches_sync(client)

    assert isinstance(response, Batches)
    assert len(response.batches) == 1


async def test_get_batches_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCH_BY_ID_URL, json=BATCHES)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_batches_async(client, batch_id="batch_1")

    assert isinstance(response, Batches)
    assert response.batches[0].id_ == "batch_1"


def test_get_batches_sync_single_batch_payload(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCH_BY_ID_URL, json=BATCHES_LIST[0])

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_batches_sync(client, batch_id="batch_1")

    assert isinstance(response, Batches)
    assert len(response.batches) == 1
