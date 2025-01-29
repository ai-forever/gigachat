from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models.threads import ThreadMessages


def _get_kwargs(
    *,
    thread_id: str,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    params: Dict[str, Any] = {"thread_id": thread_id}
    if limit:
        params["limit"] = limit
    if before:
        params["before"] = before
    params = {
        "method": "GET",
        "url": "/threads/messages",
        "headers": headers,
        "params": params,
    }
    return params


def sync(
    client: httpx.Client,
    *,
    thread_id: str,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> ThreadMessages:
    """Получение сообщений треда"""
    kwargs = _get_kwargs(thread_id=thread_id, limit=limit, before=before, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, ThreadMessages)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    thread_id: str,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> ThreadMessages:
    """Получение сообщений треда"""
    kwargs = _get_kwargs(thread_id=thread_id, limit=limit, before=before, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, ThreadMessages)
