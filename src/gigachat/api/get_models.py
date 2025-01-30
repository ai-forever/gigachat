from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models import Models


def _get_kwargs(
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": "/models",
        "headers": headers,
    }


def sync(
    client: httpx.Client,
    *,
    access_token: Optional[str] = None,
) -> Models:
    """Возвращает массив объектов с данными доступных моделей"""
    kwargs = _get_kwargs(access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Models)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    access_token: Optional[str] = None,
) -> Models:
    """Возвращает массив объектов с данными доступных моделей"""
    kwargs = _get_kwargs(access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Models)
