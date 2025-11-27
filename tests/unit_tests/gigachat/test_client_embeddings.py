import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import Embedding, Embeddings

from ...utils import get_json

BASE_URL = "http://base_url"
EMBEDDINGS_URL = f"{BASE_URL}/embeddings"

EMBEDDINGS = get_json("embeddings.json")


def test_embeddings(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.embeddings(texts=["text"], model="model")
    assert isinstance(response, Embeddings)
    for row in response.data:
        assert isinstance(row, Embedding)


@pytest.mark.asyncio()
async def test_aembeddings(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aembeddings(texts=["text"], model="model")
    assert isinstance(response, Embeddings)
    for row in response.data:
        assert isinstance(row, Embedding)

