from http import HTTPStatus
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

import httpx

from gigachat.api.utils import build_headers, build_response, build_x_headers, parse_chunk
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

EVENT_STREAM = "text/event-stream"


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
    """Получение перечня тредов"""
    kwargs = _get_threads_kwargs(
        assistants_ids=assistants_ids,
        limit=limit,
        before=before,
        access_token=access_token,
    )
    response = client.request(**kwargs)
    return build_response(response, Threads)


async def get_threads_async(
    client: httpx.AsyncClient,
    *,
    assistants_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Threads:
    """Получение перечня тредов"""
    kwargs = _get_threads_kwargs(
        assistants_ids=assistants_ids,
        limit=limit,
        before=before,
        access_token=access_token,
    )
    response = await client.request(**kwargs)
    return build_response(response, Threads)


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
    """Создание треда"""
    kwargs = _post_thread_kwargs(access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Thread)


async def post_thread_async(
    client: httpx.AsyncClient,
    *,
    access_token: Optional[str] = None,
) -> Thread:
    """Создание треда"""
    kwargs = _post_thread_kwargs(access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Thread)


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
    """Получение перечня тредов по идентификаторам"""
    kwargs = _retrieve_threads_kwargs(threads_ids=threads_ids, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Threads)


async def retrieve_threads_async(
    client: httpx.AsyncClient,
    *,
    threads_ids: List[str],
    access_token: Optional[str] = None,
) -> Threads:
    """Получение перечня тредов по идентификаторам"""
    kwargs = _retrieve_threads_kwargs(threads_ids=threads_ids, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Threads)


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
    """Удаляет тред"""
    kwargs = _delete_thread_kwargs(thread_id=thread_id, access_token=access_token)
    response = client.request(**kwargs)
    return _build_delete_response(response)


async def delete_thread_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    access_token: Optional[str] = None,
) -> bool:
    """Удаляет тред"""
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
    """Получить результат run треда"""
    kwargs = _get_thread_run_kwargs(thread_id=thread_id, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, ThreadRunResult)


async def get_thread_run_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    access_token: Optional[str] = None,
) -> ThreadRunResult:
    """Получить результат run треда"""
    kwargs = _get_thread_run_kwargs(thread_id=thread_id, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, ThreadRunResult)


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
    """Получение сообщений треда"""
    kwargs = _get_thread_messages_kwargs(thread_id=thread_id, limit=limit, before=before, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, ThreadMessages)


async def get_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> ThreadMessages:
    """Получение сообщений треда"""
    kwargs = _get_thread_messages_kwargs(thread_id=thread_id, limit=limit, before=before, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, ThreadMessages)


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
        thread_options_dict = thread_options.dict(exclude_none=True)
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
    """Получить результат run треда"""
    kwargs = _run_thread_kwargs(
        thread_id=thread_id,
        assistant_id=assistant_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    response = client.request(**kwargs)
    return build_response(response, ThreadRunResponse)


async def run_thread_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    assistant_id: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> ThreadRunResponse:
    """Получить результат run треда"""
    kwargs = _run_thread_kwargs(
        thread_id=thread_id,
        assistant_id=assistant_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    response = await client.request(**kwargs)
    return build_response(response, ThreadRunResponse)


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
        thread_options_dict = thread_options.dict(exclude_none=True)
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
    """Запуск треда с возвратом потока"""
    kwargs = _run_thread_stream_kwargs(
        thread_id=thread_id,
        assistant_id=assistant_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    with client.stream(**kwargs) as response:
        _check_response(response)
        x_headers = build_x_headers(response)
        for line in response.iter_lines():
            if chunk := parse_chunk(line, ThreadCompletionChunk):
                chunk.x_headers = x_headers
                yield chunk


async def run_thread_stream_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    assistant_id: Optional[str] = None,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> AsyncIterator[ThreadCompletionChunk]:
    """Запуск треда с возвратом потока"""
    kwargs = _run_thread_stream_kwargs(
        thread_id=thread_id,
        assistant_id=assistant_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    async with client.stream(**kwargs) as response:
        await _acheck_response(response)
        x_headers = build_x_headers(response)
        async for line in response.aiter_lines():
            if chunk := parse_chunk(line, ThreadCompletionChunk):
                chunk.x_headers = x_headers
                yield chunk


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
            "messages": [message.dict() for message in messages],
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
    """Добавление сообщений к треду без запуска"""
    kwargs = _add_thread_messages_kwargs(
        messages=messages,
        model=model,
        thread_id=thread_id,
        assistant_id=assistant_id,
        access_token=access_token,
    )
    response = client.request(**kwargs)
    return build_response(response, ThreadMessagesResponse)


async def add_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    messages: List[Messages],
    model: Optional[str] = None,
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> ThreadMessagesResponse:
    """Добавление сообщений к треду без запуска"""
    kwargs = _add_thread_messages_kwargs(
        messages=messages,
        model=model,
        thread_id=thread_id,
        assistant_id=assistant_id,
        access_token=access_token,
    )
    response = await client.request(**kwargs)
    return build_response(response, ThreadMessagesResponse)


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
        thread_options_dict = thread_options.dict(exclude_none=True, by_alias=True, exclude={"stream"})
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
                "messages": [message.dict(exclude_none=True) for message in messages],
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
    """Добавление сообщений к треду с запуском"""
    kwargs = _run_thread_messages_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        access_token=access_token,
    )
    response = client.request(**kwargs)
    return build_response(response, ThreadCompletion)


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
    """Добавление сообщений к треду с запуском"""
    kwargs = _run_thread_messages_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        access_token=access_token,
    )
    response = await client.request(**kwargs)
    return build_response(response, ThreadCompletion)


def _rerun_thread_messages_kwargs(
    *,
    thread_id: str,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    thread_options_dict = {}
    if thread_options:
        thread_options_dict = thread_options.dict(exclude_none=True, by_alias=True, exclude={"stream"})
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
    """Перегенерация ответа модели"""
    kwargs = _rerun_thread_messages_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    response = client.request(**kwargs)
    return build_response(response, ThreadCompletion)


async def rerun_thread_messages_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    thread_options: Optional[ThreadRunOptions] = None,
    access_token: Optional[str] = None,
) -> ThreadCompletion:
    """Перегенерация ответа модели"""
    kwargs = _rerun_thread_messages_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        access_token=access_token,
    )
    response = await client.request(**kwargs)
    return build_response(response, ThreadCompletion)


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
        thread_options_dict = thread_options.dict(exclude_none=True)
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
                "messages": [message.dict(exclude_none=True) for message in messages],
                "update_interval": update_interval,
                "stream": True,
            },
        },
    }


def _check_content_type(response: httpx.Response) -> None:
    content_type, _, _ = response.headers.get("content-type", "").partition(";")
    if content_type != EVENT_STREAM:
        raise httpx.TransportError(f"Expected response Content-Type to be '{EVENT_STREAM}', got {content_type!r}")


def _check_response(response: httpx.Response) -> None:
    if response.status_code == HTTPStatus.OK:
        _check_content_type(response)
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.read(), response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.read(), response.headers)


async def _acheck_response(response: httpx.Response) -> None:
    if response.status_code == HTTPStatus.OK:
        _check_content_type(response)
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, await response.aread(), response.headers)
    else:
        raise ResponseError(response.url, response.status_code, await response.aread(), response.headers)


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
    kwargs = _run_thread_messages_stream_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    with client.stream(**kwargs) as response:
        _check_response(response)
        x_headers = build_x_headers(response)
        for line in response.iter_lines():
            if chunk := parse_chunk(line, ThreadCompletionChunk):
                chunk.x_headers = x_headers
                yield chunk


async def run_thread_messages_stream_async(
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
    kwargs = _run_thread_messages_stream_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    async with client.stream(**kwargs) as response:
        await _acheck_response(response)
        x_headers = build_x_headers(response)
        async for line in response.aiter_lines():
            if chunk := parse_chunk(line, ThreadCompletionChunk):
                chunk.x_headers = x_headers
                yield chunk


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
        thread_options_dict = thread_options.dict(exclude_none=True)
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
    """Перегенерация ответа модели"""
    kwargs = _rerun_thread_messages_stream_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    with client.stream(**kwargs) as response:
        _check_response(response)
        x_headers = build_x_headers(response)
        for line in response.iter_lines():
            if chunk := parse_chunk(line, ThreadCompletionChunk):
                chunk.x_headers = x_headers
                yield chunk


async def rerun_thread_messages_stream_async(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    thread_options: Optional[ThreadRunOptions] = None,
    update_interval: Optional[int] = None,
    access_token: Optional[str] = None,
) -> AsyncIterator[ThreadCompletionChunk]:
    """Перегенерация ответа модели"""
    kwargs = _rerun_thread_messages_stream_kwargs(
        thread_id=thread_id,
        thread_options=thread_options,
        update_interval=update_interval,
        access_token=access_token,
    )
    async with client.stream(**kwargs) as response:
        await _acheck_response(response)
        x_headers = build_x_headers(response)
        async for line in response.aiter_lines():
            if chunk := parse_chunk(line, ThreadCompletionChunk):
                chunk.x_headers = x_headers
                yield chunk
