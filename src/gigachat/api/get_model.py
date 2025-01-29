from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models import Model


def _get_kwargs(
    *,
    model: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": f"/models/{model}",
        "headers": headers,
    }


def sync(
    client: httpx.Client,
    *,
    model: str,
    access_token: Optional[str] = None,
) -> Model:
    """Возвращает объект с описанием указанной модели"""
    kwargs = _get_kwargs(model=model, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Model)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    model: str,
    access_token: Optional[str] = None,
) -> Model:
    """Возвращает объект с описанием указанной модели"""
    kwargs = _get_kwargs(model=model, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Model)
