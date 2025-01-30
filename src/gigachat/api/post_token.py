from typing import Any, Dict

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models import Token


def _get_kwargs(
    *,
    user: str,
    password: str,
) -> Dict[str, Any]:
    headers = build_headers()

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
) -> Token:
    kwargs = _get_kwargs(user=user, password=password)
    response = client.request(**kwargs)
    return build_response(response, Token)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    user: str,
    password: str,
) -> Token:
    kwargs = _get_kwargs(user=user, password=password)
    response = await client.request(**kwargs)
    return build_response(response, Token)
