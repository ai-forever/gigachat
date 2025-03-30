from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models import AICheckResult


def _get_kwargs(
    *,
    input_: str,
    model: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/ai/check",
        "json": {"input": input_, "model": model},
        "headers": headers,
    }


def sync(
    client: httpx.Client,
    *,
    input_: str,
    model: str,
    access_token: Optional[str] = None,
) -> AICheckResult:
    kwargs = _get_kwargs(input_=input_, model=model, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, AICheckResult)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    input_: str,
    model: str,
    access_token: Optional[str] = None,
) -> AICheckResult:
    kwargs = _get_kwargs(input_=input_, model=model, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, AICheckResult)
