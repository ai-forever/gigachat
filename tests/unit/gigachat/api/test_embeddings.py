import json

import httpx
from pytest_httpx import HTTPXMock

from gigachat.api.embeddings import embeddings_async, embeddings_sync
from gigachat.models.embeddings import Embeddings
from tests.constants import BASE_URL, EMBEDDINGS, EMBEDDINGS_URL


def test_embeddings_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = embeddings_sync(client, input_="text", model="model")

    assert isinstance(response, Embeddings)
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"input": "text", "model": "model"}


async def test_embeddings_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await embeddings_async(client, input_=["text"], model="model")

    assert isinstance(response, Embeddings)
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"input": ["text"], "model": "model"}
