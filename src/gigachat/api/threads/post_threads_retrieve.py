from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models.threads import Threads


def _get_kwargs(
    *,
    threads_ids: List[str],
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    params = {
        "method": "POST",
        "url": "/threads/retrieve",
        "json": {
            "threads_ids": threads_ids,
        },
        "headers": headers,
    }
    return params


def sync(
    client: httpx.Client,
    *,
    threads_ids: List[str],
    access_token: Optional[str] = None,
) -> Threads:
    """Получение перечня тредов по идентификаторам"""
    kwargs = _get_kwargs(threads_ids=threads_ids, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Threads)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    threads_ids: List[str],
    access_token: Optional[str] = None,
) -> Threads:
    """Получение перечня тредов по идентификаторам"""
    kwargs = _get_kwargs(threads_ids=threads_ids, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Threads)
