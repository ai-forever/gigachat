import httpx
from pytest_httpx import HTTPXMock

from gigachat.api.assistants import (
    create_assistant_async,
    create_assistant_sync,
    delete_assistant_async,
    delete_assistant_file_async,
    delete_assistant_file_sync,
    delete_assistant_sync,
    get_assistants_async,
    get_assistants_sync,
    modify_assistant_async,
    modify_assistant_sync,
)
from gigachat.models.assistants import (
    Assistant,
    AssistantDelete,
    AssistantFileDelete,
    Assistants,
    CreateAssistant,
)
from tests.constants import (
    BASE_URL,
    GET_ASSISTANTS,
    GET_ASSISTANTS_URL,
    POST_ASSISTANT_DELETE,
    POST_ASSISTANT_DELETE_URL,
    POST_ASSISTANT_FILES_DELETE,
    POST_ASSISTANT_FILES_DELETE_URL,
    POST_ASSISTANT_MODIFY,
    POST_ASSISTANT_MODIFY_URL,
    POST_ASSISTANTS,
    POST_ASSISTANTS_URL,
)


def test_get_assistants_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_ASSISTANTS_URL, json=GET_ASSISTANTS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_assistants_sync(client)

    assert isinstance(response, Assistants)


async def test_get_assistants_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_ASSISTANTS_URL, json=GET_ASSISTANTS)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_assistants_async(client)

    assert isinstance(response, Assistants)


def test_create_assistant_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANTS_URL, json=POST_ASSISTANTS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = create_assistant_sync(client, model="model", name="name")

    assert isinstance(response, CreateAssistant)


async def test_create_assistant_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANTS_URL, json=POST_ASSISTANTS)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await create_assistant_async(client, model="model", name="name")

    assert isinstance(response, CreateAssistant)


def test_modify_assistant_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANT_MODIFY_URL, json=POST_ASSISTANT_MODIFY)

    with httpx.Client(base_url=BASE_URL) as client:
        response = modify_assistant_sync(client, assistant_id="1")

    assert isinstance(response, Assistant)


async def test_modify_assistant_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANT_MODIFY_URL, json=POST_ASSISTANT_MODIFY)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await modify_assistant_async(client, assistant_id="1")

    assert isinstance(response, Assistant)


def test_delete_assistant_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANT_DELETE_URL, json=POST_ASSISTANT_DELETE)

    with httpx.Client(base_url=BASE_URL) as client:
        response = delete_assistant_sync(client, assistant_id="1")

    assert isinstance(response, AssistantDelete)


async def test_delete_assistant_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANT_DELETE_URL, json=POST_ASSISTANT_DELETE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await delete_assistant_async(client, assistant_id="1")

    assert isinstance(response, AssistantDelete)


def test_delete_assistant_file_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANT_FILES_DELETE_URL, json=POST_ASSISTANT_FILES_DELETE)

    with httpx.Client(base_url=BASE_URL) as client:
        response = delete_assistant_file_sync(client, assistant_id="1", file_id="1")

    assert isinstance(response, AssistantFileDelete)


async def test_delete_assistant_file_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_ASSISTANT_FILES_DELETE_URL, json=POST_ASSISTANT_FILES_DELETE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await delete_assistant_file_async(client, assistant_id="1", file_id="1")

    assert isinstance(response, AssistantFileDelete)
