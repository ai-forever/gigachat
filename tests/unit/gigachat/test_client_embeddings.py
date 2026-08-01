from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import Embeddings
from tests.constants import BASE_URL, EMBEDDINGS, EMBEDDINGS_URL


def test_embeddings_accepts_single_string(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.embeddings("single input", model="Embeddings")

    assert isinstance(response, Embeddings)


async def test_aembeddings_accepts_single_string(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=EMBEDDINGS_URL, json=EMBEDDINGS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aembeddings("single input", model="Embeddings")

    assert isinstance(response, Embeddings)
