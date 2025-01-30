from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models.assistants import Assistants


def _get_kwargs(
    *,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    params = {
        "method": "GET",
        "url": "/assistants",
        "headers": headers,
    }
    if assistant_id:
        params["params"] = {"assistant_id": assistant_id}
    return params


def sync(
    client: httpx.Client,
    *,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Assistants:
    """Возвращает массив объектов с данными доступных ассистентов"""
    kwargs = _get_kwargs(assistant_id=assistant_id, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Assistants)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Assistants:
    """Возвращает массив объектов с данными доступных ассистентов"""
    kwargs = _get_kwargs(assistant_id=assistant_id, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Assistants)
