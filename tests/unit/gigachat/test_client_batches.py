from io import BytesIO
from unittest.mock import patch

from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models.batches import Batch, Batches
from tests.constants import BASE_URL

BATCHES_URL = f"{BASE_URL}/batches"
BATCH = {
    "id": "batch-1",
    "method": "chat_completions",
    "request_counts": {"total": 1},
    "status": "created",
    "created_at": 1726478395,
    "updated_at": 1726478395,
}


def test_create_batch(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=chat_completions", json=BATCH)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.create_batch('{"id":"1","request":{}}', "chat_completions")

    assert isinstance(response, Batch)


@patch("gigachat.retry.time.sleep")
def test_create_batch_retries_file_like_with_identical_body(mock_sleep: object, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=chat_completions", status_code=500)
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=chat_completions", json=BATCH)

    with GigaChatSyncClient(base_url=BASE_URL, max_retries=1, retry_backoff_factor=0) as client:
        response = client.create_batch(BytesIO(b'{"id":"1","request":{}}'), "chat_completions")

    assert isinstance(response, Batch)
    assert [request.content for request in httpx_mock.get_requests()] == [
        b'{"id":"1","request":{}}',
        b'{"id":"1","request":{}}',
    ]


def test_get_batches(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCHES_URL, json={"batches": [BATCH]})

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.get_batches()

    assert isinstance(response, Batches)


async def test_acreate_batch(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=embedder", json={**BATCH, "method": "embedder"})

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.acreate_batch(b'{"id":"1","request":{}}', "embedder")

    assert isinstance(response, Batch)


async def test_aget_batches(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?batch_id=batch-1", json={"batches": [BATCH]})

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_batches("batch-1")

    assert isinstance(response, Batches)
