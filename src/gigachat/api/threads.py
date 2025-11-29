from http import HTTPStatus
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

import httpx

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
    assistants_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    params: Dict[str, Any] = {}
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
    assistants_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
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
    assistants_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Threads:
    """Get list of threads."""
    kwargs = _get_threads_kwargs(
        assistants_ids=assistants_ids,
        limit=limit,
        before=before,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, Threads)


def _post_thread_kwargs(*, access_token: Optional[str] = None) -> Dict[str, Any]:
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
    access_token: Optional[str] = None,
) -> Thread:
    """Create thread."""
    kwargs = _post_thread_kwargs(access_token=access_token)
    return execute_request_sync(client, kwargs, Thread)


async def post_thread_async(
    client: httpx.AsyncClient,
    *,
    access_token: Optional[str] = None,
) -> Thread:
    """Create thread."""
    kwargs = _post_thread_kwargs(access_token=access_token)
    return await execute_request_async(client, kwargs, Thread)


def _retrieve_threads_kwargs(
    *,
    threads_ids: List[str],
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    threads_ids: List[str],
    access_token: Optional[str] = None,
) -> Threads:
    """Retrieve threads by IDs."""
    kwargs = _retrieve_threads_kwargs(threads_ids=threads_ids, access_token=access_token)
    return execute_request_sync(client, kwargs, Threads)


async def retrieve_threads_async(
    client: httpx.AsyncClient,
    *,
    threads_ids: List[str],
    access_token: Optional[str] = None,
) -> Threads:
    """Retrieve threads by IDs."""
    kwargs = _retrieve_threads_kwargs(threads_ids=threads_ids, access_token=access_token)
    return await execute_request_async(client, kwargs, Threads)


def _delete_thread_kwargs(
    *,
    thread_id: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    access_token: Optional[str] = None,
) -> bool:
    """Delete thread."""
    kwargs = _delete_thread_kwargs(thread_id=thread_id, access_token=access_token)
    response = client.request(**kwargs)
    return _build_delete_response(response)


async def delete_thread_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    access_token: Optional[str] = None,
) -> bool:
    """Delete thread."""
    kwargs = _delete_thread_kwargs(thread_id=thread_id, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_delete_response(response)


def _get_thread_run_kwargs(
    *,
    thread_id: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    access_token: Optional[str] = None,
) -> ThreadRunResult:
    """Get thread run status."""
    kwargs = _get_thread_run_kwargs(thread_id=thread_id, access_token=access_token)
    return execute_request_sync(client, kwargs, ThreadRunResult)


async def get_thread_run_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    access_token: Optional[str] = None,
) -> ThreadRunResult:
    """Get thread run status."""
    kwargs = _get_thread_run_kwargs(thread_id=thread_id, access_token=access_token)
    return await execute_request_async(client, kwargs, ThreadRunResult)


def _get_thread_messages_kwargs(
    *,
    thread_id: str,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    params: Dict[str, Any] = {"thread_id": thread_id}
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
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> ThreadMessages:
    """Get thread messages."""
    kwargs = _get_thread_messages_kwargs(thread_id=thread_id, limit=limit, before=before, access_token=access_token)
    return execute_request_sync(client, kwargs, ThreadMessages)


async def get_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> ThreadMessages:
    """Get thread messages."""
    kwargs = _get_thread_messages_kwargs(thread_id=thread_id, limit=limit, before=before, access_token=access_token)
    return await execute_request_async(client, kwargs, ThreadMessages)


def _run_thread_kwargs(
    *,
    thread_id: str,
    assistant_id: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    assistant_id: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
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
    assistant_id: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
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
    assistant_id: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    assistant_id: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
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
    assistant_id: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
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
    messages: List[Messages],
    model: Optional[str] = None,
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    if thread_id is not None or assistant_id is not None:
        model = None
    return {
        "method": "POST",
        "url": "/threads/messages",
        "json": {
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
    messages: List[Messages],
    model: Optional[str] = None,
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> ThreadMessagesResponse:
    """Add messages to thread."""
    kwargs = _add_thread_messages_kwargs(
        messages=messages,
        model=model,
        thread_id=thread_id,
        assistant_id=assistant_id,
        access_token=access_token,
    )
    return execute_request_sync(client, kwargs, ThreadMessagesResponse)


async def add_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    messages: List[Messages],
    model: Optional[str] = None,
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> ThreadMessagesResponse:
    """Add messages to thread."""
    kwargs = _add_thread_messages_kwargs(
        messages=messages,
        model=model,
        thread_id=thread_id,
        assistant_id=assistant_id,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, ThreadMessagesResponse)


def _run_thread_messages_kwargs(
    *,
    messages: List[Messages],
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    model: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    messages: List[Messages],
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    model: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> ThreadCompletion:
    """Add messages and run thread."""
    kwargs = _run_thread_messages_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        access_token=access_token,
    )
    return execute_request_sync(client, kwargs, ThreadCompletion)


async def run_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    messages: List[Messages],
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    model: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> ThreadCompletion:
    """Add messages and run thread."""
    kwargs = _run_thread_messages_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, ThreadCompletion)


def _rerun_thread_messages_kwargs(
    *,
    thread_id: str,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    thread_options_dict = {}
    if thread_options:
        thread_options_dict = thread_options.model_dump(exclude_none=True, by_alias=True, exclude={"stream"})
    return {
        "method": "POST",
        "url": "/threads/messages/rerun",
        "headers": headers,
        "json": {
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
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> ThreadCompletion:
    """Rerun thread messages."""
    kwargs = _rerun_thread_messages_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    return execute_request_sync(client, kwargs, ThreadCompletion)


async def rerun_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> ThreadCompletion:
    """Rerun thread messages."""
    kwargs = _rerun_thread_messages_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, ThreadCompletion)


def _run_thread_messages_stream_kwargs(
    *,
    messages: List[Messages],
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    model: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    update_interval: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    messages: List[Messages],
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    model: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    update_interval: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Iterator[ThreadCompletionChunk]:
    """Add messages and run thread with streaming."""
    kwargs = _run_thread_messages_stream_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    return execute_stream_sync(client, kwargs, ThreadCompletionChunk)


def run_thread_messages_stream_async(
    client: httpx.AsyncClient,
    *,
    messages: List[Messages],
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    model: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    update_interval: Optional[int] = None,
    access_token: Optional[str] = None,
) -> AsyncIterator[ThreadCompletionChunk]:
    """Add messages and run thread with streaming."""
    kwargs = _run_thread_messages_stream_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    return execute_stream_async(client, kwargs, ThreadCompletionChunk)


def _rerun_thread_messages_stream_kwargs(
    *,
    thread_id: str,
    thread_options: Optional[ThreadRunOptions] = None,
    update_interval: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    thread_options: Optional[ThreadRunOptions] = None,
    update_interval: Optional[int] = None,
    access_token: Optional[str] = None,
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
    thread_options: Optional[ThreadRunOptions] = None,
    update_interval: Optional[int] = None,
    access_token: Optional[str] = None,
) -> AsyncIterator[ThreadCompletionChunk]:
    """Rerun thread messages with streaming."""
    kwargs = _rerun_thread_messages_stream_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    return execute_stream_async(client, kwargs, ThreadCompletionChunk)
