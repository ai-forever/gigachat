from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.assistants import AssistantDelete


def _get_kwargs(
    *,
    assistant_id: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/assistants/delete",
        "json": {
            "assistant_id": assistant_id,
        },
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> AssistantDelete:
    if response.status_code == HTTPStatus.OK:
        return AssistantDelete(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    assistant_id: str,
    access_token: Optional[str] = None,
) -> AssistantDelete:
    kwargs = _get_kwargs(assistant_id=assistant_id, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    assistant_id: str,
    access_token: Optional[str] = None,
) -> AssistantDelete:
    kwargs = _get_kwargs(assistant_id=assistant_id, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
