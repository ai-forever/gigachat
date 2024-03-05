from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Chat, ChatCompletion


def _get_kwargs(
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/chat/completions",
        "json": chat.dict(exclude_none=True, by_alias=True, exclude={"stream"}),
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> ChatCompletion:
    if response.status_code == HTTPStatus.OK:
        return ChatCompletion(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> ChatCompletion:
    kwargs = _get_kwargs(chat=chat, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> ChatCompletion:
    kwargs = _get_kwargs(chat=chat, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
