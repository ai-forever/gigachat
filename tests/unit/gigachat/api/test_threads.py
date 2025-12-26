import httpx
from pytest_httpx import HTTPXMock

from gigachat.api.threads import (
    add_thread_messages_async,
    add_thread_messages_sync,
    delete_thread_async,
    delete_thread_sync,
    get_thread_messages_async,
    get_thread_messages_sync,
    get_thread_run_async,
    get_thread_run_sync,
    get_threads_async,
    get_threads_sync,
    post_thread_async,
    post_thread_sync,
    rerun_thread_messages_async,
    rerun_thread_messages_stream_async,
    rerun_thread_messages_stream_sync,
    rerun_thread_messages_sync,
    retrieve_threads_async,
    retrieve_threads_sync,
    run_thread_async,
    run_thread_messages_async,
    run_thread_messages_stream_async,
    run_thread_messages_stream_sync,
    run_thread_messages_sync,
    run_thread_stream_async,
    run_thread_stream_sync,
    run_thread_sync,
)
from gigachat.models.chat import Messages
from gigachat.models.threads import (
    Thread,
    ThreadCompletion,
    ThreadCompletionChunk,
    ThreadMessages,
    ThreadMessagesResponse,
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
    THREAD,
)


def test_get_threads_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_URL, json=GET_THREADS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_threads_sync(client)

    assert isinstance(response, Threads)


async def test_get_threads_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_URL, json=GET_THREADS)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_threads_async(client)

    assert isinstance(response, Threads)


def test_post_thread_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_URL, json=THREAD)

    with httpx.Client(base_url=BASE_URL) as client:
        response = post_thread_sync(client)

    assert isinstance(response, Thread)


async def test_post_thread_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_URL, json=THREAD)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await post_thread_async(client)

    assert isinstance(response, Thread)


def test_retrieve_threads_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_RETRIEVE_URL, json=POST_THREADS_RETRIEVE)

    with httpx.Client(base_url=BASE_URL) as client:
        response = retrieve_threads_sync(client, threads_ids=["1"])

    assert isinstance(response, Threads)


async def test_retrieve_threads_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_RETRIEVE_URL, json=POST_THREADS_RETRIEVE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await retrieve_threads_async(client, threads_ids=["1"])

    assert isinstance(response, Threads)


def test_delete_thread_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_DELETE_URL, content=POST_THREADS_DELETE)

    with httpx.Client(base_url=BASE_URL) as client:
        response = delete_thread_sync(client, thread_id="1")

    assert response is True


async def test_delete_thread_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_DELETE_URL, content=POST_THREADS_DELETE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await delete_thread_async(client, thread_id="1")

    assert response is True


def test_get_thread_run_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_RUN_URL, json=GET_THREADS_RUN)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_thread_run_sync(client, thread_id="111")

    assert isinstance(response, ThreadRunResult)


async def test_get_thread_run_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_RUN_URL, json=GET_THREADS_RUN)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_thread_run_async(client, thread_id="111")

    assert isinstance(response, ThreadRunResult)


def test_get_thread_messages_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_MESSAGES_URL, json=GET_THREADS_MESSAGES)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_thread_messages_sync(client, thread_id="111")

    assert isinstance(response, ThreadMessages)


async def test_get_thread_messages_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=GET_THREADS_MESSAGES_URL, json=GET_THREADS_MESSAGES)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_thread_messages_async(client, thread_id="111")

    assert isinstance(response, ThreadMessages)


def test_run_thread_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_RUN_URL, json=POST_THREADS_RUN)

    with httpx.Client(base_url=BASE_URL) as client:
        response = run_thread_sync(client, thread_id="1")

    assert isinstance(response, ThreadRunResponse)


async def test_run_thread_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_RUN_URL, json=POST_THREADS_RUN)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await run_thread_async(client, thread_id="1")

    assert isinstance(response, ThreadRunResponse)


def test_run_thread_stream_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=POST_THREADS_RUN_URL,
        content=POST_THREAD_MESSAGES_RUN_STREAM,
        headers=HEADERS_STREAM,
    )

    with httpx.Client(base_url=BASE_URL) as client:
        response = list(run_thread_stream_sync(client, thread_id="1"))

    assert len(response) == 2
    assert all(isinstance(chunk, ThreadCompletionChunk) for chunk in response)


async def test_run_thread_stream_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=POST_THREADS_RUN_URL,
        content=POST_THREAD_MESSAGES_RUN_STREAM,
        headers=HEADERS_STREAM,
    )

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = [chunk async for chunk in run_thread_stream_async(client, thread_id="1")]

    assert len(response) == 2
    assert all(isinstance(chunk, ThreadCompletionChunk) for chunk in response)


def test_add_thread_messages_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_MESSAGES_URL, json=POST_THREADS_MESSAGES)

    with httpx.Client(base_url=BASE_URL) as client:
        response = add_thread_messages_sync(
            client,
            thread_id="1",
            messages=[Messages(role="user", content="text")],
        )

    assert isinstance(response, ThreadMessagesResponse)


async def test_add_thread_messages_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREADS_MESSAGES_URL, json=POST_THREADS_MESSAGES)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await add_thread_messages_async(
            client,
            thread_id="1",
            messages=[Messages(role="user", content="text")],
        )

    assert isinstance(response, ThreadMessagesResponse)


def test_run_thread_messages_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREAD_MESSAGES_RUN_URL, json=POST_THREAD_MESSAGES_RUN)

    with httpx.Client(base_url=BASE_URL) as client:
        response = run_thread_messages_sync(
            client,
            thread_id="1",
            messages=[Messages(role="user", content="text")],
        )

    assert isinstance(response, ThreadCompletion)


async def test_run_thread_messages_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREAD_MESSAGES_RUN_URL, json=POST_THREAD_MESSAGES_RUN)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await run_thread_messages_async(
            client,
            thread_id="1",
            messages=[Messages(role="user", content="text")],
        )

    assert isinstance(response, ThreadCompletion)


def test_rerun_thread_messages_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREAD_MESSAGES_RERUN_URL, json=POST_THREAD_MESSAGES_RERUN)

    with httpx.Client(base_url=BASE_URL) as client:
        response = rerun_thread_messages_sync(client, thread_id="1")

    assert isinstance(response, ThreadCompletion)


async def test_rerun_thread_messages_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=POST_THREAD_MESSAGES_RERUN_URL, json=POST_THREAD_MESSAGES_RERUN)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await rerun_thread_messages_async(client, thread_id="1")

    assert isinstance(response, ThreadCompletion)


def test_run_thread_messages_stream_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=POST_THREAD_MESSAGES_RUN_URL,
        content=POST_THREAD_MESSAGES_RUN_STREAM,
        headers=HEADERS_STREAM,
    )

    with httpx.Client(base_url=BASE_URL) as client:
        response = list(
            run_thread_messages_stream_sync(
                client,
                thread_id="1",
                messages=[Messages(role="user", content="text")],
            )
        )

    assert len(response) == 2
    assert all(isinstance(chunk, ThreadCompletionChunk) for chunk in response)


async def test_run_thread_messages_stream_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=POST_THREAD_MESSAGES_RUN_URL,
        content=POST_THREAD_MESSAGES_RUN_STREAM,
        headers=HEADERS_STREAM,
    )

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = [
            chunk
            async for chunk in run_thread_messages_stream_async(
                client,
                thread_id="1",
                messages=[Messages(role="user", content="text")],
            )
        ]

    assert len(response) == 2
    assert all(isinstance(chunk, ThreadCompletionChunk) for chunk in response)


def test_rerun_thread_messages_stream_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=POST_THREAD_MESSAGES_RERUN_URL,
        content=POST_THREAD_MESSAGES_RERUN_STREAM,
        headers=HEADERS_STREAM,
    )

    with httpx.Client(base_url=BASE_URL) as client:
        response = list(rerun_thread_messages_stream_sync(client, thread_id="1"))

    assert len(response) == 73
    assert all(isinstance(chunk, ThreadCompletionChunk) for chunk in response)


async def test_rerun_thread_messages_stream_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=POST_THREAD_MESSAGES_RERUN_URL,
        content=POST_THREAD_MESSAGES_RERUN_STREAM,
        headers=HEADERS_STREAM,
    )

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = [chunk async for chunk in rerun_thread_messages_stream_async(client, thread_id="1")]

    assert len(response) == 73
    assert all(isinstance(chunk, ThreadCompletionChunk) for chunk in response)
