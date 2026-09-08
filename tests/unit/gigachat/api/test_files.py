from typing import Type

import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api.files import (
    _delete_file_kwargs,
    _get_file_content_kwargs,
    _get_file_kwargs,
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
from gigachat.exceptions import NotFoundError, RateLimitError, ResponseError, ServerError
from gigachat.models.files import DeletedFile, DownloadedFile, Image, UploadedFile, UploadedFiles
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


def test_file_path_parameters_are_percent_encoded() -> None:
    value = "a/b?x=1#frag"
    encoded = "a%2Fb%3Fx%3D1%23frag"

    assert _get_file_kwargs(file=value)["url"] == f"/files/{encoded}"
    assert _delete_file_kwargs(file=value)["url"] == f"/files/{encoded}/delete"
    assert _get_file_content_kwargs(file_id=value)["url"] == f"/files/{encoded}/content"


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
    request = httpx_mock.get_request()
    assert request is not None
    assert request.content == b""
    assert "content-type" not in request.headers


async def test_delete_file_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILE_DELETE_URL, json=FILE_DELETE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await delete_file_async(client, file="1")

    assert isinstance(response, DeletedFile)
    request = httpx_mock.get_request()
    assert request is not None
    assert request.content == b""
    assert "content-type" not in request.headers


def test_get_file_content_sync_preserves_binary_and_metadata(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=IMAGE_URL,
        content=FILE_CONTENT,
        headers={
            "content-type": "application/octet-stream",
            "content-disposition": 'attachment; filename="scene.fbx"',
            "x-request-id": "request-1",
        },
    )

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_file_content_sync(client, file_id="img_file")

    assert isinstance(response, DownloadedFile)
    assert response.content == FILE_CONTENT
    assert response.content_type == "application/octet-stream"
    assert response.content_disposition == 'attachment; filename="scene.fbx"'
    assert response.x_headers is not None
    assert response.x_headers["x-request-id"] == "request-1"
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers.get("accept") != "application/jpg"


async def test_get_file_content_async_preserves_binary_and_metadata(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=IMAGE_URL,
        content=FILE_CONTENT,
        headers={"content-type": "model/fbx", "x-session-id": "session-1"},
    )

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_file_content_async(client, file_id="img_file")

    assert isinstance(response, DownloadedFile)
    assert response.content == FILE_CONTENT
    assert response.content_type == "model/fbx"
    assert response.x_headers is not None
    assert response.x_headers["x-session-id"] == "session-1"


@pytest.mark.parametrize(
    ("status_code", "exception_type"),
    [(404, NotFoundError), (429, RateLimitError), (500, ServerError)],
)
def test_get_file_content_sync_maps_http_errors(
    httpx_mock: HTTPXMock,
    status_code: int,
    exception_type: Type[ResponseError],
) -> None:
    httpx_mock.add_response(url=IMAGE_URL, status_code=status_code, headers={"retry-after": "0"})

    with httpx.Client(base_url=BASE_URL) as client, pytest.raises(exception_type):
        get_file_content_sync(client, file_id="img_file")


@pytest.mark.parametrize(
    ("status_code", "exception_type"),
    [(404, NotFoundError), (429, RateLimitError), (500, ServerError)],
)
async def test_get_file_content_async_maps_http_errors(
    httpx_mock: HTTPXMock,
    status_code: int,
    exception_type: Type[ResponseError],
) -> None:
    httpx_mock.add_response(url=IMAGE_URL, status_code=status_code, headers={"retry-after": "0"})

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        with pytest.raises(exception_type):
            await get_file_content_async(client, file_id="img_file")


def test_get_image_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_image_sync(client, file_id="img_file")

    assert isinstance(response, Image)
    assert response.content


def test_get_image_sync_maps_http_errors(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, status_code=404)

    with httpx.Client(base_url=BASE_URL) as client, pytest.raises(NotFoundError):
        get_image_sync(client, file_id="img_file")


async def test_get_image_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_image_async(client, file_id="img_file")

    assert isinstance(response, Image)
    assert response.content
