import httpx
from pytest_httpx import HTTPXMock

from gigachat.api.files import (
    delete_file_async,
    delete_file_sync,
    get_file_async,
    get_file_content_async,
    get_file_content_sync,
    get_file_sync,
    get_files_async,
    get_files_sync,
    get_image_async,
    get_image_sync,
    upload_file_async,
    upload_file_sync,
)
from gigachat.models.files import DeletedFile, File, UploadedFile, UploadedFiles
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


def test_get_file_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILE_URL, json=GET_FILE)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_file_sync(client, file="1")

    assert isinstance(response, UploadedFile)


async def test_get_file_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILE_URL, json=GET_FILE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_file_async(client, file="1")

    assert isinstance(response, UploadedFile)


def test_get_files_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILES_URL, json=GET_FILES)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_files_sync(client)

    assert isinstance(response, UploadedFiles)


async def test_get_files_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILES_URL, json=GET_FILES)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_files_async(client)

    assert isinstance(response, UploadedFiles)


def test_upload_file_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILES_URL, json=FILES)

    with httpx.Client(base_url=BASE_URL) as client:
        response = upload_file_sync(client, file=FILE)

    assert isinstance(response, UploadedFile)


async def test_upload_file_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILES_URL, json=FILES)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await upload_file_async(client, file=FILE)

    assert isinstance(response, UploadedFile)


def test_delete_file_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILE_DELETE_URL, json=FILE_DELETE)

    with httpx.Client(base_url=BASE_URL) as client:
        response = delete_file_sync(client, file="1")

    assert isinstance(response, DeletedFile)


async def test_delete_file_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILE_DELETE_URL, json=FILE_DELETE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await delete_file_async(client, file="1")

    assert isinstance(response, DeletedFile)


def test_get_image_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_file_content_sync(client, file_id="img_file")

    assert isinstance(response, File)
    assert response.content


async def test_get_image_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_file_content_async(client, file_id="img_file")

    assert isinstance(response, File)
    assert response.content


def test_get_image_sync_deprecated(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_image_sync(client, file_id="img_file")

    assert isinstance(response, File)
    assert response.content


async def test_get_image_async_deprecated(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_image_async(client, file_id="img_file")

    assert isinstance(response, File)
    assert response.content
