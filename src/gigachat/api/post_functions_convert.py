from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
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


def sync(
    client: httpx.Client,
    *,
    openapi_function: str,
    access_token: Optional[str] = None,
) -> OpenApiFunctions:
    """Конвертация описание функции в формате OpenAPI в gigachat функцию"""
    kwargs = _get_kwargs(openapi_function=openapi_function, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, OpenApiFunctions)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    openapi_function: str,
    access_token: Optional[str] = None,
) -> OpenApiFunctions:
    """Конвертация описание функции в формате OpenAPI в gigachat функцию"""
    kwargs = _get_kwargs(openapi_function=openapi_function, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, OpenApiFunctions)
