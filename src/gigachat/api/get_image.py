import base64
from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Image


def _get_kwargs(
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Accept"] = "application/jpg"
    return {
        "method": "GET",
        "url": f"/files/{file_id}/content",
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> Image:
    if response.status_code == HTTPStatus.OK:
        return Image(content=base64.b64encode(response.content))
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> Image:
    """Возвращает изображение в base64 кодировке"""
    kwargs = _get_kwargs(access_token=access_token, file_id=file_id)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> Image:
    """Возвращает изображение в base64 кодировке"""
    kwargs = _get_kwargs(access_token=access_token, file_id=file_id)
    response = await client.request(**kwargs)
    return _build_response(response)
