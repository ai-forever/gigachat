from http import HTTPStatus
from typing import Any, Dict, Optional

import httpx

from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import AccessToken


def _get_kwargs(*, url: str, credentials: str, scope: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {credentials}",
    }

    if request_id:
        headers["RqUID"] = request_id

    return {
        "method": "POST",
        "url": url,
        "data": {"scope": scope},
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> AccessToken:
    if response.status_code == HTTPStatus.OK:
        return AccessToken(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client, *, url: str, credentials: str, scope: str, request_id: Optional[str] = None
) -> AccessToken:
    kwargs = _get_kwargs(url=url, credentials=credentials, scope=scope, request_id=request_id)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient, *, url: str, credentials: str, scope: str, request_id: Optional[str] = None
) -> AccessToken:
    kwargs = _get_kwargs(url=url, credentials=credentials, scope=scope, request_id=request_id)
    response = await client.request(**kwargs)
    return _build_response(response)
