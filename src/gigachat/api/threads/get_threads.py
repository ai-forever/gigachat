from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models.threads import Threads


def _get_kwargs(
    *,
    assistants_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    params: Dict[str, Any] = {}
    if assistants_ids:
        params["assistants_ids"] = assistants_ids
    if limit:
        params["limit"] = limit
    if before:
        params["before"] = before
    params = {
        "method": "GET",
        "url": "/threads",
        "headers": headers,
        "params": params,
    }
    return params


def sync(
    client: httpx.Client,
    *,
    assistants_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Threads:
    """Получение перечня тредов"""
    kwargs = _get_kwargs(
        assistants_ids=assistants_ids,
        limit=limit,
        before=before,
        access_token=access_token,
    )
    response = client.request(**kwargs)
    return build_response(response, Threads)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    assistants_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    before: Optional[int] = None,
    access_token: Optional[str] = None,
) -> Threads:
    """Получение перечня тредов"""
    kwargs = _get_kwargs(
        assistants_ids=assistants_ids,
        limit=limit,
        before=before,
        access_token=access_token,
    )
    response = await client.request(**kwargs)
    return build_response(response, Threads)
