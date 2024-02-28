from http import HTTPStatus
from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import TokensCount


def _get_kwargs(
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    json_data = {"model": model, "input": input_}

    return {
        "method": "POST",
        "url": "/tokens/count",
        "headers": headers,
        "json": json_data,
    }


def _build_response(response: httpx.Response) -> List[TokensCount]:
    if response.status_code == HTTPStatus.OK:
        return [TokensCount(**row) for row in response.json()]
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(
    client: httpx.Client,
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> List[TokensCount]:
    """Возвращает объект с информацией о количестве токенов"""
    kwargs = _get_kwargs(input_=input_, model=model, access_token=access_token)
    response = client.request(**kwargs)
    return _build_response(response)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> List[TokensCount]:
    """Возвращает объект с информацией о количестве токенов"""
    kwargs = _get_kwargs(input_=input_, model=model, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_response(response)
