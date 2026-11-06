from collections.abc import AsyncIterator, Iterator
from http import HTTPStatus
from typing import Any

import httpx2 as httpx

from gigachat._core.execution import request_async, request_sync
from gigachat.api.utils import (
    build_headers,
    execute_request_async,
    execute_request_sync,
    execute_stream_async,
    execute_stream_sync,
)
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.chat import Messages
from gigachat.models.threads import (
    SharedThread,
    Thread,
    ThreadCompletion,
    ThreadCompletionChunk,
    ThreadMessages,
    ThreadMessagesResponse,
    ThreadRunOptions,
    ThreadRunResponse,
    ThreadRunResult,
    Threads,
)


def _get_threads_kwargs(
    *,
    assistants_ids: list[str] | None = None,
    limit: int | None = None,
    before: int | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    params: dict[str, Any] = {}
    if assistants_ids:
        params["assistants_ids"] = assistants_ids
    if limit:
        params["limit"] = limit
    if before:
        params["before"] = before
    return {
        "method": "GET",
        "url": "/threads",
        "headers": headers,
        "params": params,
    }


def get_threads_sync(
    client: httpx.Client,
    *,
    assistants_ids: list[str] | None = None,
    limit: int | None = None,
    before: int | None = None,
    access_token: str | None = None,
) -> Threads:
    """Get list of threads."""
    kwargs = _get_threads_kwargs(
        assistants_ids=assistants_ids,
        limit=limit,
        before=before,
        access_token=access_token,
    )
    return execute_request_sync(client, kwargs, Threads)


async def get_threads_async(
    client: httpx.AsyncClient,
    *,
    assistants_ids: list[str] | None = None,
    limit: int | None = None,
    before: int | None = None,
    access_token: str | None = None,
) -> Threads:
    """Get list of threads."""
    kwargs = _get_threads_kwargs(
        assistants_ids=assistants_ids,
        limit=limit,
        before=before,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, Threads)


def _post_thread_kwargs(*, access_token: str | None = None) -> dict[str, Any]:
    headers = build_headers(access_token)
    return {
        "method": "POST",
        "url": "/threads",
        "headers": headers,
        "json": {},
    }


def post_thread_sync(
    client: httpx.Client,
    *,
    access_token: str | None = None,
) -> Thread:
    """Create thread."""
    kwargs = _post_thread_kwargs(access_token=access_token)
    return execute_request_sync(client, kwargs, Thread)


async def post_thread_async(
    client: httpx.AsyncClient,
    *,
    access_token: str | None = None,
) -> Thread:
    """Create thread."""
    kwargs = _post_thread_kwargs(access_token=access_token)
    return await execute_request_async(client, kwargs, Thread)


def _retrieve_threads_kwargs(
    *,
    threads_ids: list[str],
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    return {
        "method": "POST",
        "url": "/threads/retrieve",
        "json": {
            "threads_ids": threads_ids,
        },
        "headers": headers,
    }


def retrieve_threads_sync(
    client: httpx.Client,
    *,
    threads_ids: list[str],
    access_token: str | None = None,
) -> Threads:
    """Retrieve threads by IDs."""
    kwargs = _retrieve_threads_kwargs(threads_ids=threads_ids, access_token=access_token)
    return execute_request_sync(client, kwargs, Threads)


async def retrieve_threads_async(
    client: httpx.AsyncClient,
    *,
    threads_ids: list[str],
    access_token: str | None = None,
) -> Threads:
    """Retrieve threads by IDs."""
    kwargs = _retrieve_threads_kwargs(threads_ids=threads_ids, access_token=access_token)
    return await execute_request_async(client, kwargs, Threads)


def _delete_thread_kwargs(
    *,
    thread_id: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    return {
        "method": "POST",
        "url": "/threads/delete",
        "json": {
            "thread_id": thread_id,
        },
        "headers": headers,
    }


def _build_delete_response(response: httpx.Response) -> bool:
    if response.status_code == HTTPStatus.OK:
        return True
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def delete_thread_sync(
    client: httpx.Client,
    *,
    thread_id: str,
    access_token: str | None = None,
) -> bool:
    """Delete thread."""
    kwargs = _delete_thread_kwargs(thread_id=thread_id, access_token=access_token)
    response = request_sync(client, **kwargs)
    return _build_delete_response(response)


async def delete_thread_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    access_token: str | None = None,
) -> bool:
    """Delete thread."""
    kwargs = _delete_thread_kwargs(thread_id=thread_id, access_token=access_token)
    response = await request_async(client, **kwargs)
    return _build_delete_response(response)


def _get_thread_run_kwargs(
    *,
    thread_id: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    return {
        "method": "GET",
        "url": "/threads/run",
        "headers": headers,
        "params": {"thread_id": thread_id},
    }


def get_thread_run_sync(
    client: httpx.Client,
    *,
    thread_id: str,
    access_token: str | None = None,
) -> ThreadRunResult:
    """Get thread run status."""
    kwargs = _get_thread_run_kwargs(thread_id=thread_id, access_token=access_token)
    return execute_request_sync(client, kwargs, ThreadRunResult)


async def get_thread_run_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    access_token: str | None = None,
) -> ThreadRunResult:
    """Get thread run status."""
    kwargs = _get_thread_run_kwargs(thread_id=thread_id, access_token=access_token)
    return await execute_request_async(client, kwargs, ThreadRunResult)


def _get_thread_messages_kwargs(
    *,
    thread_id: str,
    limit: int | None = None,
    before: int | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    params: dict[str, Any] = {"thread_id": thread_id}
    if limit:
        params["limit"] = limit
    if before:
        params["before"] = before
    return {
        "method": "GET",
        "url": "/threads/messages",
        "headers": headers,
        "params": params,
    }


def get_thread_messages_sync(
    client: httpx.Client,
    *,
    thread_id: str,
    limit: int | None = None,
    before: int | None = None,
    access_token: str | None = None,
) -> ThreadMessages:
    """Get thread messages."""
    kwargs = _get_thread_messages_kwargs(thread_id=thread_id, limit=limit, before=before, access_token=access_token)
    return execute_request_sync(client, kwargs, ThreadMessages)


async def get_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    limit: int | None = None,
    before: int | None = None,
    access_token: str | None = None,
) -> ThreadMessages:
    """Get thread messages."""
    kwargs = _get_thread_messages_kwargs(thread_id=thread_id, limit=limit, before=before, access_token=access_token)
    return await execute_request_async(client, kwargs, ThreadMessages)


def _run_thread_kwargs(
    *,
    thread_id: str,
    assistant_id: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    thread_options_dict = {}
    if thread_options:
        thread_options_dict = thread_options.model_dump(exclude_none=True)
    return {
        "method": "POST",
        "url": "/threads/run",
        "headers": headers,
        "json": {**thread_options_dict, **{"thread_id": thread_id, "assistant_id": assistant_id}},
    }


def run_thread_sync(
    client: httpx.Client,
    *,
    thread_id: str,
    assistant_id: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    access_token: str | None = None,
) -> ThreadRunResponse:
    """Run thread."""
    kwargs = _run_thread_kwargs(
        thread_id=thread_id,
        assistant_id=assistant_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    return execute_request_sync(client, kwargs, ThreadRunResponse)


async def run_thread_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    assistant_id: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    access_token: str | None = None,
) -> ThreadRunResponse:
    """Run thread."""
    kwargs = _run_thread_kwargs(
        thread_id=thread_id,
        assistant_id=assistant_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, ThreadRunResponse)


def _run_thread_stream_kwargs(
    *,
    thread_id: str,
    assistant_id: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    thread_options_dict = {}
    if thread_options:
        thread_options_dict = thread_options.model_dump(exclude_none=True)
    return {
        "method": "POST",
        "url": "/threads/run",
        "headers": headers,
        "json": {
            **thread_options_dict,
            **{"thread_id": thread_id, "assistant_id": assistant_id, "stream": True},
        },
    }


def run_thread_stream_sync(
    client: httpx.Client,
    *,
    thread_id: str,
    assistant_id: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    access_token: str | None = None,
) -> Iterator[ThreadCompletionChunk]:
    """Run thread with streaming."""
    kwargs = _run_thread_stream_kwargs(
        thread_id=thread_id,
        assistant_id=assistant_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    return execute_stream_sync(client, kwargs, ThreadCompletionChunk)


def run_thread_stream_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    assistant_id: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    access_token: str | None = None,
) -> AsyncIterator[ThreadCompletionChunk]:
    """Run thread with streaming."""
    kwargs = _run_thread_stream_kwargs(
        thread_id=thread_id,
        assistant_id=assistant_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    return execute_stream_async(client, kwargs, ThreadCompletionChunk)


def _add_thread_messages_kwargs(
    *,
    messages: list[Messages],
    model: str | None = None,
    thread_id: str | None = None,
    assistant_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    if thread_id is not None or assistant_id is not None:
        model = None
    return {
        "method": "POST",
        "url": "/threads/messages",
        "json": {
            **({"metadata": metadata} if metadata is not None else {}),
            "thread_id": thread_id,
            "model": model,
            "assistant_id": assistant_id,
            "messages": [message.model_dump() for message in messages],
        },
        "headers": headers,
    }


def add_thread_messages_sync(
    client: httpx.Client,
    *,
    messages: list[Messages],
    model: str | None = None,
    thread_id: str | None = None,
    assistant_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> ThreadMessagesResponse:
    """Add messages to thread."""
    kwargs = _add_thread_messages_kwargs(
        messages=messages,
        model=model,
        thread_id=thread_id,
        assistant_id=assistant_id,
        metadata=metadata,
        access_token=access_token,
    )
    return execute_request_sync(client, kwargs, ThreadMessagesResponse)


async def add_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    messages: list[Messages],
    model: str | None = None,
    thread_id: str | None = None,
    assistant_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> ThreadMessagesResponse:
    """Add messages to thread."""
    kwargs = _add_thread_messages_kwargs(
        messages=messages,
        model=model,
        thread_id=thread_id,
        assistant_id=assistant_id,
        metadata=metadata,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, ThreadMessagesResponse)


def _run_thread_messages_kwargs(
    *,
    messages: list[Messages],
    thread_id: str | None = None,
    assistant_id: str | None = None,
    model: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    metadata: dict[str, Any] | None = None,
    update_interval: float | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    thread_options_dict = {}
    if thread_options:
        thread_options_dict = thread_options.model_dump(exclude_none=True, by_alias=True, exclude={"stream"})
    if thread_id is not None or assistant_id is not None:
        model = None
    return {
        "method": "POST",
        "url": "/threads/messages/run",
        "headers": headers,
        "json": {
            **({"update_interval": update_interval} if update_interval is not None else {}),
            **({"metadata": metadata} if metadata is not None else {}),
            **thread_options_dict,
            **{
                "thread_id": thread_id,
                "assistant_id": assistant_id,
                "model": model,
                "messages": [message.model_dump(exclude_none=True) for message in messages],
            },
        },
    }


def run_thread_messages_sync(
    client: httpx.Client,
    *,
    messages: list[Messages],
    thread_id: str | None = None,
    assistant_id: str | None = None,
    model: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    metadata: dict[str, Any] | None = None,
    update_interval: float | None = None,
    access_token: str | None = None,
) -> ThreadCompletion:
    """Add messages and run thread."""
    kwargs = _run_thread_messages_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        metadata=metadata,
        update_interval=update_interval,
        access_token=access_token,
    )
    return execute_request_sync(client, kwargs, ThreadCompletion)


async def run_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    messages: list[Messages],
    thread_id: str | None = None,
    assistant_id: str | None = None,
    model: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    metadata: dict[str, Any] | None = None,
    update_interval: float | None = None,
    access_token: str | None = None,
) -> ThreadCompletion:
    """Add messages and run thread."""
    kwargs = _run_thread_messages_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        metadata=metadata,
        update_interval=update_interval,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, ThreadCompletion)


def _rerun_thread_messages_kwargs(
    *,
    thread_id: str,
    thread_options: ThreadRunOptions | None = None,
    update_interval: float | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    thread_options_dict = {}
    if thread_options:
        thread_options_dict = thread_options.model_dump(exclude_none=True, by_alias=True, exclude={"stream"})
    return {
        "method": "POST",
        "url": "/threads/messages/rerun",
        "headers": headers,
        "json": {
            **({"update_interval": update_interval} if update_interval is not None else {}),
            **thread_options_dict,
            **{
                "thread_id": thread_id,
            },
        },
    }


def rerun_thread_messages_sync(
    client: httpx.Client,
    *,
    thread_id: str,
    thread_options: ThreadRunOptions | None = None,
    update_interval: float | None = None,
    access_token: str | None = None,
) -> ThreadCompletion:
    """Rerun thread messages."""
    kwargs = _rerun_thread_messages_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    return execute_request_sync(client, kwargs, ThreadCompletion)


async def rerun_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    thread_options: ThreadRunOptions | None = None,
    update_interval: float | None = None,
    access_token: str | None = None,
) -> ThreadCompletion:
    """Rerun thread messages."""
    kwargs = _rerun_thread_messages_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, ThreadCompletion)


def _run_thread_messages_stream_kwargs(
    *,
    messages: list[Messages],
    thread_id: str | None = None,
    assistant_id: str | None = None,
    model: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    update_interval: float | None = None,
    metadata: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    thread_options_dict = {}
    if assistant_id is not None or thread_id is not None:
        model = None
    if thread_options:
        thread_options_dict = thread_options.model_dump(exclude_none=True)
    return {
        "method": "POST",
        "url": "/threads/messages/run",
        "headers": headers,
        "json": {
            **({"metadata": metadata} if metadata is not None else {}),
            **thread_options_dict,
            **{
                "thread_id": thread_id,
                "assistant_id": assistant_id,
                "model": model,
                "messages": [message.model_dump(exclude_none=True) for message in messages],
                "update_interval": update_interval,
                "stream": True,
            },
        },
    }


def run_thread_messages_stream_sync(
    client: httpx.Client,
    *,
    messages: list[Messages],
    thread_id: str | None = None,
    assistant_id: str | None = None,
    model: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    update_interval: float | None = None,
    metadata: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> Iterator[ThreadCompletionChunk]:
    """Add messages and run thread with streaming."""
    kwargs = _run_thread_messages_stream_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        update_interval=update_interval,
        metadata=metadata,
        access_token=access_token,
    )
    return execute_stream_sync(client, kwargs, ThreadCompletionChunk)


def run_thread_messages_stream_async(
    client: httpx.AsyncClient,
    *,
    messages: list[Messages],
    thread_id: str | None = None,
    assistant_id: str | None = None,
    model: str | None = None,
    thread_options: ThreadRunOptions | None = None,
    update_interval: float | None = None,
    metadata: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> AsyncIterator[ThreadCompletionChunk]:
    """Add messages and run thread with streaming."""
    kwargs = _run_thread_messages_stream_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        update_interval=update_interval,
        metadata=metadata,
        access_token=access_token,
    )
    return execute_stream_async(client, kwargs, ThreadCompletionChunk)


def _rerun_thread_messages_stream_kwargs(
    *,
    thread_id: str,
    thread_options: ThreadRunOptions | None = None,
    update_interval: float | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    thread_options_dict = {}
    if thread_options:
        thread_options_dict = thread_options.model_dump(exclude_none=True)
    return {
        "method": "POST",
        "url": "/threads/messages/rerun",
        "headers": headers,
        "json": {
            **thread_options_dict,
            **{
                "thread_id": thread_id,
                "update_interval": update_interval,
                "stream": True,
            },
        },
    }


def rerun_thread_messages_stream_sync(
    client: httpx.Client,
    *,
    thread_id: str,
    thread_options: ThreadRunOptions | None = None,
    update_interval: float | None = None,
    access_token: str | None = None,
) -> Iterator[ThreadCompletionChunk]:
    """Rerun thread messages with streaming."""
    kwargs = _rerun_thread_messages_stream_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    return execute_stream_sync(client, kwargs, ThreadCompletionChunk)


def rerun_thread_messages_stream_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    thread_options: ThreadRunOptions | None = None,
    update_interval: float | None = None,
    access_token: str | None = None,
) -> AsyncIterator[ThreadCompletionChunk]:
    """Rerun thread messages with streaming."""
    kwargs = _rerun_thread_messages_stream_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    return execute_stream_async(client, kwargs, ThreadCompletionChunk)


def share_thread_sync(client: httpx.Client, *, thread_id: str, access_token: str | None = None) -> SharedThread:
    """Create a read-only shared copy of a thread."""
    kwargs = _get_share_thread_kwargs(thread_id=thread_id, access_token=access_token)
    return execute_request_sync(client, kwargs, SharedThread)


async def share_thread_async(
    client: httpx.AsyncClient, *, thread_id: str, access_token: str | None = None
) -> SharedThread:
    """Create a read-only shared copy of a thread."""
    kwargs = _get_share_thread_kwargs(thread_id=thread_id, access_token=access_token)
    return await execute_request_async(client, kwargs, SharedThread)


def _get_share_thread_kwargs(*, thread_id: str, access_token: str | None) -> dict[str, Any]:
    return {
        "method": "POST",
        "url": "/threads/share",
        "headers": build_headers(access_token),
        "json": {"thread_id": thread_id},
    }
