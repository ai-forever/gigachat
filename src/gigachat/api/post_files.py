from http import HTTPStatus
from typing import Any, Dict, Literal, Optional

import httpx

from gigachat._types import FileTypes
from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import UploadedFile


def _get_kwargs(
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/files",
        "files": {"file": file},
        "data": {"purpose": purpose},
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> UploadedFile:
    if response.status_code == HTTPStatus.OK:
        return UploadedFile(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: Optional[str] = None,
) -> UploadedFile:
    kwargs = _get_kwargs(file=file, purpose=purpose, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: Optional[str] = None,
) -> UploadedFile:
    kwargs = _get_kwargs(file=file, purpose=purpose, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
