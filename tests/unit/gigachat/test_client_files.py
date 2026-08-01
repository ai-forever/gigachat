from pathlib import Path
from unittest.mock import patch

from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import DeletedFile, DownloadedFile, Image, UploadedFile, UploadedFiles
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

FILE_CONTENT = b"Kaydara FBX Binary  \x00\x1a\x00"


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


def test_get_file_content(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=FILE_CONTENT, headers={"content-type": "model/fbx"})

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.get_file_content(file_id="img_file")

    assert isinstance(response, DownloadedFile)
    assert response.content == FILE_CONTENT
    assert response.content_type == "model/fbx"


def test_download_file_saves_raw_content(httpx_mock: HTTPXMock, tmp_path: Path) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=FILE_CONTENT, headers={"content-type": "model/fbx"})

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        output = client.download_file(file_id="img_file", path=tmp_path / "scene.fbx")

    assert output == tmp_path / "scene.fbx"
    assert output.read_bytes() == FILE_CONTENT


@patch("gigachat.retry.time.sleep")
def test_get_file_content_retries_server_error(mock_sleep: object, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, status_code=500)
    httpx_mock.add_response(url=IMAGE_URL, content=FILE_CONTENT, headers={"content-type": "model/fbx"})

    with GigaChatSyncClient(base_url=BASE_URL, max_retries=1, retry_backoff_factor=0) as client:
        response = client.get_file_content(file_id="img_file")

    assert isinstance(response, DownloadedFile)
    assert response.content == FILE_CONTENT
    assert len(httpx_mock.get_requests()) == 2


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
        response = await client.aget_image(file_id="img_file")

    assert isinstance(response, Image)


async def test_aget_file_content(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=FILE_CONTENT, headers={"content-type": "model/fbx"})

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_file_content(file_id="img_file")

    assert isinstance(response, DownloadedFile)
    assert response.content == FILE_CONTENT
    assert response.content_type == "model/fbx"


async def test_adownload_file_saves_raw_content(httpx_mock: HTTPXMock, tmp_path: Path) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=FILE_CONTENT, headers={"content-type": "model/fbx"})

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        output = await client.adownload_file(file_id="img_file", path=str(tmp_path / "scene.fbx"))

    assert output == tmp_path / "scene.fbx"
    assert output.read_bytes() == FILE_CONTENT
