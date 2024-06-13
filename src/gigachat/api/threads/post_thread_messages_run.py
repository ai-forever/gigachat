from http import HTTPStatus
from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Messages
from gigachat.models.threads import ThreadCompletion, ThreadRunOptions


def _get_kwargs(
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
    params = {
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
    return params


def _build_response(response: httpx.Response) -> ThreadCompletion:
    if response.status_code == HTTPStatus.OK:
        return ThreadCompletion(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
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
    kwargs = _get_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        access_token=access_token,
    )
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
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
    kwargs = _get_kwargs(
        messages=messages,
        thread_id=thread_id,
        assistant_id=assistant_id,
        model=model,
        thread_options=thread_options,
        access_token=access_token,
    )
    response = await client.request(**kwargs)
    return _build_response(response)
