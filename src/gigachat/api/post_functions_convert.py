from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.open_api_functions import OpenApiFunctions


def _get_kwargs(
    *,
    openapi_function: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/functions/convert",
        "content": openapi_function,
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> OpenApiFunctions:
    if response.status_code == HTTPStatus.OK:
        return OpenApiFunctions(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    openapi_function: str,
    access_token: Optional[str] = None,
) -> OpenApiFunctions:
    """Конвертация описание функции в формате OpenAPI в gigachat функцию"""
    kwargs = _get_kwargs(openapi_function=openapi_function, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    openapi_function: str,
    access_token: Optional[str] = None,
) -> OpenApiFunctions:
    """Конвертация описание функции в формате OpenAPI в gigachat функцию"""
    kwargs = _get_kwargs(openapi_function=openapi_function, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
