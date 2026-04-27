import warnings

import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import DeletedFile, File, UploadedFile, UploadedFiles
from gigachat.resources.files import FilesAsyncResource, FilesSyncResource
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


def test_files_resource_is_cached_property() -> None:
    client = GigaChatSyncClient()

    assert "files" not in client.__dict__

    resource = client.files

    assert resource is client.files
    assert isinstance(resource, FilesSyncResource)


async def test_a_files_resource_is_cached_property() -> None:
    client = GigaChatAsyncClient()

    assert "a_files" not in client.__dict__

    resource = client.a_files

    assert resource is client.a_files
    assert isinstance(resource, FilesAsyncResource)


def test_files_upload(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILES_URL, json=FILES)

    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.files.upload(file=FILE)

    assert isinstance(response, UploadedFile)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_files_retrieve(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILE_URL, json=GET_FILE)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.files.retrieve(file="1")

    assert isinstance(response, UploadedFile)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_files_list(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILES_URL, json=GET_FILES)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.files.list()

    assert isinstance(response, UploadedFiles)
    assert len(response.data) == 2
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_files_delete(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILE_DELETE_URL, json=FILE_DELETE)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.files.delete(file="1")

    assert isinstance(response, DeletedFile)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_files_retrieve_content(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.files.retrieve_content(file_id="img_file")

    assert isinstance(response, File)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_files_retrieve_image_deprecated_alias(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.files\.retrieve_content\(\.\.\.\)"):
            response = client.files.retrieve_image(file_id="img_file")

    assert isinstance(response, File)


def test_upload_file_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILES_URL, json=FILES)

    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.files\.upload\(\.\.\.\)"):
            response = client.upload_file(file=FILE)

    assert isinstance(response, UploadedFile)


def test_get_file_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILE_URL, json=GET_FILE)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.files\.retrieve\(\.\.\.\)"):
            response = client.get_file(file="1")

    assert isinstance(response, UploadedFile)


def test_get_files_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILES_URL, json=GET_FILES)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.files\.list\(\)"):
            response = client.get_files()

    assert isinstance(response, UploadedFiles)
    assert len(response.data) == 2


def test_delete_file_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILE_DELETE_URL, json=FILE_DELETE)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.files\.delete\(\.\.\.\)"):
            response = client.delete_file(file="1")

    assert isinstance(response, DeletedFile)


def test_get_file_content_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.files\.retrieve_content\(\.\.\.\)"):
            response = client.get_file_content(file_id="img_file")

    assert isinstance(response, File)


def test_get_image_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.files\.retrieve_content\(\.\.\.\)"):
            response = client.get_image(file_id="img_file")

    assert isinstance(response, File)


async def test_a_files_upload(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILES_URL, json=FILES)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_files.upload(file=FILE)

    assert isinstance(response, UploadedFile)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_a_files_retrieve(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILE_URL, json=GET_FILE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_files.retrieve(file="1")

    assert isinstance(response, UploadedFile)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_a_files_list(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILES_URL, json=GET_FILES)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_files.list()

    assert isinstance(response, UploadedFiles)
    assert len(response.data) == 2
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_a_files_delete(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILE_DELETE_URL, json=FILE_DELETE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_files.delete(file="1")

    assert isinstance(response, DeletedFile)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_a_files_retrieve_content(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    async with GigaChatAsyncClient(base_url=BASE_URL, model="model") as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_files.retrieve_content(file_id="img_file")

    assert isinstance(response, File)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_a_files_retrieve_image_deprecated_alias(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    async with GigaChatAsyncClient(base_url=BASE_URL, model="model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_files\.retrieve_content\(\.\.\.\)"):
            response = await client.a_files.retrieve_image(file_id="img_file")

    assert isinstance(response, File)


async def test_aupload_file_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILES_URL, json=FILES)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_files\.upload\(\.\.\.\)"):
            response = await client.aupload_file(file=FILE)

    assert isinstance(response, UploadedFile)


async def test_aget_file_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILE_URL, json=GET_FILE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_files\.retrieve\(\.\.\.\)"):
            response = await client.aget_file(file="1")

    assert isinstance(response, UploadedFile)


async def test_aget_files_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_FILES_URL, json=GET_FILES)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_files\.list\(\)"):
            response = await client.aget_files()

    assert isinstance(response, UploadedFiles)
    assert len(response.data) == 2


async def test_adelete_file_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILE_DELETE_URL, json=FILE_DELETE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_files\.delete\(\.\.\.\)"):
            response = await client.adelete_file(file="1")

    assert isinstance(response, DeletedFile)


async def test_aget_file_content_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    async with GigaChatAsyncClient(base_url=BASE_URL, model="model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_files\.retrieve_content\(\.\.\.\)"):
            response = await client.aget_file_content(file_id="img_file")

    assert isinstance(response, File)


async def test_aget_image_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=IMAGE_URL, content=IMAGE)
    async with GigaChatAsyncClient(base_url=BASE_URL, model="model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_files\.retrieve_content\(\.\.\.\)"):
            response = await client.aget_image(file_id="img_file")

    assert isinstance(response, File)
