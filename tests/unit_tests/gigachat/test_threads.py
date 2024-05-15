import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models.threads import (
    ThreadCompletion,
    ThreadCompletionChunk,
    ThreadMessages,
    ThreadMessagesResponse,
    ThreadRunOptions,
    ThreadRunResponse,
    ThreadRunResult,
    Threads,
)

from ...utils import get_bytes, get_json

BASE_URL = "http://base_url"

GET_THREADS_URL = f"{BASE_URL}/threads"
GET_THREADS_MESSAGES_URL = f"{BASE_URL}/threads/messages?thread_id=111"
GET_THREADS_RUN_URL = f"{BASE_URL}/threads/run?thread_id=111"
POST_THREAD_MESSAGES_RERUN_URL = f"{BASE_URL}/threads/messages/rerun"
POST_THREAD_MESSAGES_RUN_URL = f"{BASE_URL}/threads/messages/run"
POST_THREADS_DELETE_URL = f"{BASE_URL}/threads/delete"
POST_THREADS_MESSAGES_URL = f"{BASE_URL}/threads/messages"
POST_THREADS_RUN_URL = f"{BASE_URL}/threads/run"

GET_THREADS = get_json("threads/get_threads.json")
GET_THREADS_MESSAGES = get_json("threads/get_threads_messages.json")
GET_THREADS_RUN = get_json("threads/get_threads_run.json")
POST_THREAD_MESSAGES_RERUN = get_json("threads/post_thread_messages_rerun.json")
POST_THREAD_MESSAGES_RERUN_STREAM = get_bytes("threads/post_thread_messages_rerun.stream")
POST_THREAD_MESSAGES_RUN = get_json("threads/post_thread_messages_run.json")
POST_THREAD_MESSAGES_RUN_STREAM = get_bytes("threads/post_thread_messages_run.stream")
POST_THREADS_DELETE = get_bytes("threads/post_threads_delete.txt")
POST_THREADS_MESSAGES = get_json("threads/post_threads_messages.json")
POST_THREADS_RUN = get_json("threads/post_threads_run.json")

HEADERS_STREAM = {"Content-Type": "text/event-stream"}


def test_get_threads(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_URL, json=GET_THREADS)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.list()

    assert isinstance(response, Threads)
    assert len(response.threads) == 3


@pytest.mark.asyncio()
async def test_aget_threads(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_URL, json=GET_THREADS)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_threads.list()

    assert isinstance(response, Threads)
    assert len(response.threads) == 3


def test_get_threads_messages(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_MESSAGES_URL, json=GET_THREADS_MESSAGES)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.get_messages(thread_id="111")

    assert isinstance(response, ThreadMessages)
    assert len(response.messages) == 2


@pytest.mark.asyncio()
async def test_aget_threads_messages(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_MESSAGES_URL, json=GET_THREADS_MESSAGES)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_threads.get_messages(thread_id="111")

    assert isinstance(response, ThreadMessages)
    assert len(response.messages) == 2


def test_get_threads_run(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_RUN_URL, json=GET_THREADS_RUN)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.get_run(thread_id="111")

    assert isinstance(response, ThreadRunResult)
    assert len(response.messages) == 2  # type: ignore


@pytest.mark.asyncio()
async def test_aget_threads_run(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_RUN_URL, json=GET_THREADS_RUN)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_threads.get_run(thread_id="111")

    assert isinstance(response, ThreadRunResult)
    assert len(response.messages) == 2  # type: ignore


def test_post_thread_messages_rerun(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREAD_MESSAGES_RERUN_URL, json=POST_THREAD_MESSAGES_RERUN)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.rerun_messages(thread_id="111", thread_options=ThreadRunOptions(temperature=0.1))

    assert isinstance(response, ThreadCompletion)


@pytest.mark.asyncio()
async def test_apost_thread_messages_rerun(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREAD_MESSAGES_RERUN_URL, json=POST_THREAD_MESSAGES_RERUN)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_threads.rerun_messages(
            thread_id="111", thread_options=ThreadRunOptions(temperature=0.1)
        )

    assert isinstance(response, ThreadCompletion)


def test_post_thread_messages_run(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREAD_MESSAGES_RUN_URL, json=POST_THREAD_MESSAGES_RUN)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.run_messages(messages=[""], thread_options=ThreadRunOptions(temperature=0.1))

    assert isinstance(response, ThreadCompletion)


@pytest.mark.asyncio()
async def test_apost_thread_messages_run(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREAD_MESSAGES_RUN_URL, json=POST_THREAD_MESSAGES_RUN)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_threads.run_messages(messages=[""], thread_options=ThreadRunOptions(temperature=0.1))

    assert isinstance(response, ThreadCompletion)


def test_post_thread_messages(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_MESSAGES_URL, json=POST_THREADS_MESSAGES)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.add_messages(messages=[""])

    assert isinstance(response, ThreadMessagesResponse)


@pytest.mark.asyncio()
async def test_apost_thread_messages(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_MESSAGES_URL, json=POST_THREADS_MESSAGES)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_threads.add_messages(messages=[""])

    assert isinstance(response, ThreadMessagesResponse)


def test_post_threads_run(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_RUN_URL, json=POST_THREADS_RUN)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.run(thread_id="111", thread_options=ThreadRunOptions(temperature=0.1))

    assert isinstance(response, ThreadRunResponse)


@pytest.mark.asyncio()
async def test_apost_threads_run(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_RUN_URL, json=POST_THREADS_RUN)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_threads.run(thread_id="111", thread_options=ThreadRunOptions(temperature=0.1))

    assert isinstance(response, ThreadRunResponse)


def test_post_threads_delete(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_DELETE_URL, content=POST_THREADS_DELETE)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.delete(thread_id="111")

    assert isinstance(response, bool)


@pytest.mark.asyncio()
async def test_apost_threads_delete(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_DELETE_URL, content=POST_THREADS_DELETE)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_threads.delete(thread_id="111")

    assert isinstance(response, bool)


def test_post_thread_messages_rerun_stream(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=POST_THREAD_MESSAGES_RERUN_URL,
        content=POST_THREAD_MESSAGES_RERUN_STREAM,
        headers=HEADERS_STREAM,
    )
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = list(
            client.threads.rerun_messages_stream(thread_id="111", thread_options=ThreadRunOptions(temperature=0.1))
        )

    assert all(isinstance(chunk, ThreadCompletionChunk) for chunk in response)
    assert len(response) == 73


@pytest.mark.asyncio()
async def test_apost_thread_messages_rerun_stream(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=POST_THREAD_MESSAGES_RERUN_URL,
        content=POST_THREAD_MESSAGES_RERUN_STREAM,
        headers=HEADERS_STREAM,
    )
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = [
            chunk
            async for chunk in client.a_threads.rerun_messages_stream(
                thread_id="111", thread_options=ThreadRunOptions(temperature=0.1)
            )
        ]

    assert all(isinstance(chunk, ThreadCompletionChunk) for chunk in response)
    assert len(response) == 73


def test_post_thread_messages_run_stream(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=POST_THREAD_MESSAGES_RUN_URL,
        content=POST_THREAD_MESSAGES_RUN_STREAM,
        headers=HEADERS_STREAM,
    )
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = list(
            client.threads.run_messages_stream(messages=[""], thread_options=ThreadRunOptions(temperature=0.1))
        )

    assert all(isinstance(chunk, ThreadCompletionChunk) for chunk in response)
    assert len(response) == 2


@pytest.mark.asyncio()
async def test_apost_thread_messages_run_stream(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=POST_THREAD_MESSAGES_RUN_URL,
        content=POST_THREAD_MESSAGES_RUN_STREAM,
        headers=HEADERS_STREAM,
    )
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = [
            chunk
            async for chunk in client.a_threads.run_messages_stream(
                messages=[""], thread_options=ThreadRunOptions(temperature=0.1)
            )
        ]

    assert all(isinstance(chunk, ThreadCompletionChunk) for chunk in response)
    assert len(response) == 2
