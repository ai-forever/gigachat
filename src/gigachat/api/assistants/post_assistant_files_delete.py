from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.assistants import AssistantFileDelete


def _get_kwargs(
    *,
    assistant_id: str,
    file_id: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/assistants/files/delete",
        "json": {
            "assistant_id": assistant_id,
            "file_id": file_id,
        },
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> AssistantFileDelete:
    if response.status_code == HTTPStatus.OK:
        return AssistantFileDelete(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    assistant_id: str,
    file_id: str,
    access_token: Optional[str] = None,
) -> AssistantFileDelete:
    kwargs = _get_kwargs(assistant_id=assistant_id, file_id=file_id, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    assistant_id: str,
    file_id: str,
    access_token: Optional[str] = None,
) -> AssistantFileDelete:
    kwargs = _get_kwargs(assistant_id=assistant_id, file_id=file_id, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
