import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatSyncClient, GigaChatAsyncClient
from gigachat.models import Image
from ...utils import get_bytes

BASE_URL = "http://base_url"
IMAGE_URL = f"{BASE_URL}/files/img_file/content"
IMAGE = get_bytes('image.jpg')


def test_get_image(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        response = client.get_image(file_id="img_file")

    assert isinstance(response, Image)


@pytest.mark.asyncio
async def test_aget_image(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    async with GigaChatAsyncClient(base_url=BASE_URL, model="model") as client:
        response = await client.aget_image(file_id="img_file")

    assert isinstance(response, Image)
