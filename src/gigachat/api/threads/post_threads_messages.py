from http import HTTPStatus
from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Messages
from gigachat.models.threads import ThreadMessagesResponse


def _get_kwargs(
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
    params = {
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
    return params


def _build_response(response: httpx.Response) -> ThreadMessagesResponse:
    if response.status_code == HTTPStatus.OK:
        return ThreadMessagesResponse(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    messages: List[Messages],
    model: Optional[str] = None,
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> ThreadMessagesResponse:
    """Добавление сообщений к треду без запуска"""
    kwargs = _get_kwargs(
        messages=messages,
        model=model,
        thread_id=thread_id,
        assistant_id=assistant_id,
        access_token=access_token,
    )
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    messages: List[Messages],
    model: Optional[str] = None,
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> ThreadMessagesResponse:
    """Добавление сообщений к треду без запуска"""
    kwargs = _get_kwargs(
        messages=messages,
        model=model,
        thread_id=thread_id,
        assistant_id=assistant_id,
        access_token=access_token,
    )
    response = await client.request(**kwargs)
    return _build_response(response)
