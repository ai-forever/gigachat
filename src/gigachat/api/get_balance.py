from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models.balance import Balance


def _get_kwargs(
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": "/balance",
        "headers": headers,
    }


def sync(
    client: httpx.Client,
    *,
    access_token: Optional[str] = None,
) -> Balance:
    """Метод для получения баланса доступных для использования токенов.
    Только для клиентов с предоплатой иначе http 403"""
    kwargs = _get_kwargs(access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Balance)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    access_token: Optional[str] = None,
) -> Balance:
    """Метод для получения баланса доступных для использования токенов.
    Только для клиентов с предоплатой иначе http 403"""
    kwargs = _get_kwargs(access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Balance)
