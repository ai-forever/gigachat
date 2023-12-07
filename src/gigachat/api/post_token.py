from http import HTTPStatus
from typing import Any, Dict

import httpx

from gigachat.context import operation_id_cvar, request_id_cvar, service_id_cvar, session_id_cvar
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Token


def _get_kwargs(
    *,
    user: str,
    password: str,
) -> Dict[str, Any]:
    headers = {}

    session_id = session_id_cvar.get()
    request_id = request_id_cvar.get()
    service_id = service_id_cvar.get()
    operation_id = operation_id_cvar.get()

    if session_id:
        headers["X-Session-ID"] = session_id
    if request_id:
        headers["X-Request-ID"] = request_id
    if service_id:
        headers["X-Service-ID"] = service_id
    if operation_id:
        headers["X-Operation-ID"] = operation_id

    return {
        "method": "POST",
        "url": "/token",
        "auth": (user, password),
        "headers": headers,
    }


def _build_response(response: httpx.Response) -> Token:
    if response.status_code == HTTPStatus.OK:
        return Token(**response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    user: str,
    password: str,
) -> Token:
    kwargs = _get_kwargs(user=user, password=password)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    user: str,
    password: str,
) -> Token:
    kwargs = _get_kwargs(user=user, password=password)
    response = await client.request(**kwargs)
    return _build_response(response)
