import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import DeletedFile, Image, UploadedFile, UploadedFiles

from ...utils import get_bytes, get_json

BASE_URL = "http://base_url"
FILES_URL = f"{BASE_URL}/files"
GET_FILE_URL = f"{BASE_URL}/files/1"
GET_FILES_URL = f"{BASE_URL}/files"
FILE_DELETE_URL = f"{BASE_URL}/files/1/delete"
IMAGE_URL = f"{BASE_URL}/files/img_file/content"

FILES = get_json("post_files.json")
GET_FILE = get_json("get_file.json")
GET_FILES = get_json("get_files.json")
FILE_DELETE = get_json("post_files_delete.json")

FILE = get_bytes("image.jpg")
IMAGE = get_bytes("image.jpg")


def test_upload_file(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILES_URL, json=FILES)

    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        response = client.upload_file(file=FILE)

    assert isinstance(response, UploadedFile)


def test_get_file(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILE_URL, json=GET_FILE)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.get_file(file="1")
    assert isinstance(response, UploadedFile)


def test_get_files(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILES_URL, json=GET_FILES)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.get_files()
    assert isinstance(response, UploadedFiles)
    assert len(response.data) == 2


def test_delete_file(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILE_DELETE_URL, json=FILE_DELETE)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.delete_file(file="1")
    assert isinstance(response, DeletedFile)


def test_get_image(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        response = client.get_image(file_id="img_file")

    assert isinstance(response, Image)


@pytest.mark.asyncio()
async def test_aupload_file(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILES_URL, json=FILES)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aupload_file(file=FILE)

    assert isinstance(response, UploadedFile)


@pytest.mark.asyncio()
async def test_aget_file(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILE_URL, json=GET_FILE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_file(file="1")
    assert isinstance(response, UploadedFile)


@pytest.mark.asyncio()
async def test_aget_files(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILES_URL, json=GET_FILES)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_files()
    assert isinstance(response, UploadedFiles)
    assert len(response.data) == 2


@pytest.mark.asyncio()
async def test_adelete_file(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILE_DELETE_URL, json=FILE_DELETE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.adelete_file(file="1")
    assert isinstance(response, DeletedFile)


@pytest.mark.asyncio()
async def test_aget_image(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    async with GigaChatAsyncClient(base_url=BASE_URL, model="model") as client:
        response = await client.aget_image(file_id="img_file")

    assert isinstance(response, Image)

