from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import DeletedFile, UploadedFile, UploadedFiles
from gigachat.models.files import File
from tests.constants import (
    BASE_URL,
    FILE,
    FILE_DELETE,
    FILE_DELETE_URL,
    FILES,
    FILES_URL,
    GET_FILE,
    GET_FILE_URL,
    GET_FILES,
    GET_FILES_URL,
    IMAGE,
    IMAGE_URL,
)


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
        response = client.get_file_content(file_id="img_file")

    assert isinstance(response, File)


async def test_aupload_file(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILES_URL, json=FILES)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aupload_file(file=FILE)

    assert isinstance(response, UploadedFile)


async def test_aget_file(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILE_URL, json=GET_FILE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_file(file="1")
    assert isinstance(response, UploadedFile)


async def test_aget_files(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILES_URL, json=GET_FILES)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_files()
    assert isinstance(response, UploadedFiles)
    assert len(response.data) == 2


async def test_adelete_file(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILE_DELETE_URL, json=FILE_DELETE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.adelete_file(file="1")
    assert isinstance(response, DeletedFile)


async def test_aget_image(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    async with GigaChatAsyncClient(base_url=BASE_URL, model="model") as client:
        response = await client.aget_file_content(file_id="img_file")

    assert isinstance(response, File)


def test_get_image_deprecated(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        response = client.get_image(file_id="img_file")

    assert isinstance(response, File)


async def test_aget_image_deprecated(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    async with GigaChatAsyncClient(base_url=BASE_URL, model="model") as client:
        response = await client.aget_image(file_id="img_file")

    assert isinstance(response, File)
