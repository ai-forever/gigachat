from http import HTTPStatus
from typing import Any, Dict, Optional, List

import httpx

from gigachat.context import (
    authorization_cvar,
    client_id_cvar,
    operation_id_cvar,
    request_id_cvar,
    service_id_cvar,
    session_id_cvar,
)
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import TokensCount


def _get_kwargs(
    *,
    input: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = {}

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    authorization = authorization_cvar.get()
    client_id = client_id_cvar.get()
    session_id = session_id_cvar.get()
    request_id = request_id_cvar.get()
    service_id = service_id_cvar.get()
    operation_id = operation_id_cvar.get()

    if authorization:
        headers["Authorization"] = authorization
    if client_id:
        headers["X-Client-ID"] = client_id
    if session_id:
        headers["X-Session-ID"] = session_id
    if request_id:
        headers["X-Request-ID"] = request_id
    if service_id:
        headers["X-Service-ID"] = service_id
    if operation_id:
        headers["X-Operation-ID"] = operation_id
    json_data = {"model": model, "input": input}

    return {
        "method": "POST",
        "url": "/tokens/count",
        "headers": headers,
        "json": json_data
    }


def _build_response(response: httpx.Response) -> List[TokensCount]:
    print(response.json()[0])
    if response.status_code == HTTPStatus.OK:
        return [TokensCount(**row) for row in response.json()]
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    input: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> List[TokensCount]:
    """Возвращает объект с информацией о количестве токенов"""
    kwargs = _get_kwargs(access_token=access_token, input=input, model=model)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    input: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> List[TokensCount]:
    """Возвращает объект с информацией о количестве токенов"""
    kwargs = _get_kwargs(access_token=access_token, input=input, model=model)
    response = await client.request(**kwargs)
    return _build_response(response)
