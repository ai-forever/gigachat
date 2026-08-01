from io import BytesIO

import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api.batches import create_batch_async, create_batch_sync, get_batches_async, get_batches_sync
from gigachat.exceptions import NotFoundError
from gigachat.models.batches import Batch, Batches
from tests.constants import BASE_URL

BATCHES_URL = f"{BASE_URL}/batches"
BATCH = {
    "id": "batch-1",
    "method": "chat_completions",
    "request_counts": {"total": 3},
    "status": "created",
    "created_at": 1726478395,
    "updated_at": 1726478395,
}
BATCHES = {
    "batches": [
        {
            **BATCH,
            "request_counts": {"total": 3, "completed": 2, "failed": 1},
            "status": "completed",
            "output_file_id": "file-1",
            "updated_at": 1726478474,
        }
    ]
}


def test_create_batch_sync_sends_jsonl_bytes(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=chat_completions", json=BATCH)

    with httpx.Client(base_url=BASE_URL) as client:
        response = create_batch_sync(client, file='{"id":"1","request":{}}', method="chat_completions")

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["Content-Type"] == "application/octet-stream"
    assert request.content == b'{"id":"1","request":{}}'
    assert isinstance(response, Batch)


def test_create_batch_sync_reads_file_like(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=embedder", json={**BATCH, "method": "embedder"})

    with httpx.Client(base_url=BASE_URL) as client:
        response = create_batch_sync(client, file=BytesIO(b'{"id":"1"}'), method="embedder")

    request = httpx_mock.get_request()
    assert request is not None
    assert request.content == b'{"id":"1"}'
    assert response.method.value == "embedder"


async def test_create_batch_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?method=embedder", json={**BATCH, "method": "embedder"})

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await create_batch_async(client, file=b'{"id":"1"}', method="embedder")

    assert isinstance(response, Batch)


def test_get_batches_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BATCHES_URL, json=BATCHES, headers={"x-request-id": "request-1"})

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_batches_sync(client)

    assert isinstance(response, Batches)
    assert response.x_headers is not None
    assert response.x_headers["x-request-id"] == "request-1"
    assert response.batches[0].output_file_id == "file-1"


@pytest.mark.parametrize("payload", [BATCH, [BATCH], {"batches": [BATCH]}])
def test_get_batches_sync_normalizes_documented_and_observed_payloads(httpx_mock: HTTPXMock, payload: object) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?batch_id=batch-1", json=payload)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_batches_sync(client, batch_id="batch-1")

    assert [batch.id_ for batch in response.batches] == ["batch-1"]


async def test_get_batches_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?batch_id=batch-1", json=BATCHES)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_batches_async(client, batch_id="batch-1")

    assert isinstance(response, Batches)


def test_get_batches_maps_not_found(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BATCHES_URL}?batch_id=missing", status_code=404, json={"message": "not found"})

    with httpx.Client(base_url=BASE_URL) as client, pytest.raises(NotFoundError):
        get_batches_sync(client, batch_id="missing")
