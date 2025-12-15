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
from tests.constants import (
    BASE_URL,
    GET_THREADS,
    GET_THREADS_MESSAGES,
    GET_THREADS_MESSAGES_URL,
    GET_THREADS_RUN,
    GET_THREADS_RUN_URL,
    GET_THREADS_URL,
    HEADERS_STREAM,
    POST_THREAD_MESSAGES_RERUN,
    POST_THREAD_MESSAGES_RERUN_STREAM,
    POST_THREAD_MESSAGES_RERUN_URL,
    POST_THREAD_MESSAGES_RUN,
    POST_THREAD_MESSAGES_RUN_STREAM,
    POST_THREAD_MESSAGES_RUN_URL,
    POST_THREADS_DELETE,
    POST_THREADS_DELETE_URL,
    POST_THREADS_MESSAGES,
    POST_THREADS_MESSAGES_URL,
    POST_THREADS_RETRIEVE,
    POST_THREADS_RETRIEVE_URL,
    POST_THREADS_RUN,
    POST_THREADS_RUN_URL,
)


def test_get_threads(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_URL, json=GET_THREADS)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.list()

    assert isinstance(response, Threads)
    assert len(response.threads) == 3


async def test_aget_threads(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_URL, json=GET_THREADS)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_threads.list()

    assert isinstance(response, Threads)
    assert len(response.threads) == 3


def test_post_threads_retrieve(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_RETRIEVE_URL, json=POST_THREADS_RETRIEVE)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.retrieve(threads_ids=[])

    assert isinstance(response, Threads)
    assert len(response.threads) == 1


async def test_apost_threads_retrieve(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_RETRIEVE_URL, json=POST_THREADS_RETRIEVE)
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.a_threads.retrieve(threads_ids=[])

    assert isinstance(response, Threads)
    assert len(response.threads) == 1


def test_get_threads_messages(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_MESSAGES_URL, json=GET_THREADS_MESSAGES)
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.threads.get_messages(thread_id="111")

    assert isinstance(response, ThreadMessages)
    assert len(response.messages) == 2


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
