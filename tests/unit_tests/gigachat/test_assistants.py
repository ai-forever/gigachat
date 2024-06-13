import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models.assistants import (
    Assistant,
    AssistantFileDelete,
    Assistants,
    CreateAssistant,
)

from ...utils import get_json

BASE_URL = "http://base_url"

GET_ASSISTANTS_URL = f"{BASE_URL}/assistants"
POST_ASSISTANTS_URL = f"{BASE_URL}/assistants"
POST_ASSISTANT_MODIFY_URL = f"{BASE_URL}/assistants/modify"
POST_ASSISTANT_FILES_DELETE_URL = f"{BASE_URL}/assistants/files/delete"

GET_ASSISTANTS = get_json("assistants/get_assistants.json")
POST_ASSISTANTS = get_json("assistants/post_assistants.json")
POST_ASSISTANT_MODIFY = get_json("assistants/post_assistant_modify.json")
POST_ASSISTANT_FILES_DELETE = get_json("assistants/post_assistant_files_delete.json")


def test_get_assistants(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_ASSISTANTS_URL, json=GET_ASSISTANTS)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.assistants.get()

    assert isinstance(response, Assistants)
    assert len(response.data) == 2


@pytest.mark.asyncio()
async def test_aget_assistants(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_ASSISTANTS_URL, json=GET_ASSISTANTS)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_assistants.get()

    assert isinstance(response, Assistants)
    assert len(response.data) == 2


def test_post_assistants(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANTS_URL, json=POST_ASSISTANTS)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.assistants.create(model="GigaChat", name="name", instructions="123")

    assert isinstance(response, CreateAssistant)
    assert response.assistant_id == "111"


@pytest.mark.asyncio()
async def test_apost_assistants(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANTS_URL, json=POST_ASSISTANTS)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_assistants.create(model="GigaChat", name="name", instructions="123")

    assert isinstance(response, CreateAssistant)
    assert response.assistant_id == "111"


def test_post_assistant_modify(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANT_MODIFY_URL, json=POST_ASSISTANT_MODIFY)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.assistants.update(assistant_id="111")

    assert isinstance(response, Assistant)


@pytest.mark.asyncio()
async def test_apost_assistant_modify(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANT_MODIFY_URL, json=POST_ASSISTANT_MODIFY)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_assistants.update(assistant_id="111")

    assert isinstance(response, Assistant)


def test_post_assistant_files_delete(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANT_FILES_DELETE_URL, json=POST_ASSISTANT_FILES_DELETE)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.assistants.delete_file(assistant_id="111", file_id="222")

    assert isinstance(response, AssistantFileDelete)


@pytest.mark.asyncio()
async def test_apost_assistant_files_delete(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANT_FILES_DELETE_URL, json=POST_ASSISTANT_FILES_DELETE)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_assistants.delete_file(assistant_id="111", file_id="222")

    assert isinstance(response, AssistantFileDelete)
