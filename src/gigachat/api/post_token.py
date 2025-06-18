from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models import Token


def _get_kwargs(
    *,
    user: str,
    password: str,
    custom_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    headers = build_headers(custom_headers=custom_headers)

    return {
        "method": "POST",
        "url": "/token",
        "auth": (user, password),
        "headers": headers,
    }


def sync(
    client: httpx.Client,
    *,
    user: str,
    password: str,
    custom_headers: Optional[Dict[str, str]] = None,
) -> Token:
    kwargs = _get_kwargs(user=user, password=password, custom_headers=custom_headers)
    response = client.request(**kwargs)
    return build_response(response, Token)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    user: str,
    password: str,
    custom_headers: Optional[Dict[str, str]] = None,
) -> Token:
    kwargs = _get_kwargs(user=user, password=password, custom_headers=custom_headers)
    response = await client.request(**kwargs)
    return build_response(response, Token)
