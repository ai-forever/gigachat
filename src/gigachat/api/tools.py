import json
from http import HTTPStatus
from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.tools import AICheckResult, Balance, OpenApiFunctions, TokensCount


def _get_tokens_count_kwargs(
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/json"

    json_data = {"model": model, "input": input_}

    return {
        "method": "POST",
        "url": "/tokens/count",
        "headers": headers,
        "content": json.dumps(json_data, ensure_ascii=False),
    }


def _build_tokens_count_response(response: httpx.Response) -> List[TokensCount]:
    if response.status_code == HTTPStatus.OK:
        return [TokensCount(**row) for row in response.json()]
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def tokens_count_sync(
    client: httpx.Client,
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> List[TokensCount]:
    """Возвращает объект с информацией о количестве токенов"""
    kwargs = _get_tokens_count_kwargs(input_=input_, model=model, access_token=access_token)
    response = client.request(**kwargs)
    return _build_tokens_count_response(response)


async def tokens_count_async(
    client: httpx.AsyncClient,
    *,
    input_: List[str],
    model: str,
    access_token: Optional[str] = None,
) -> List[TokensCount]:
    """Возвращает объект с информацией о количестве токенов"""
    kwargs = _get_tokens_count_kwargs(input_=input_, model=model, access_token=access_token)
    response = await client.request(**kwargs)
    return _build_tokens_count_response(response)


def _get_functions_convert_kwargs(
    *,
    openapi_function: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/functions/convert",
        "content": openapi_function,
        "headers": headers,
    }


def functions_convert_sync(
    client: httpx.Client,
    *,
    openapi_function: str,
    access_token: Optional[str] = None,
) -> OpenApiFunctions:
    """Конвертация описание функции в формате OpenAPI в gigachat функцию"""
    kwargs = _get_functions_convert_kwargs(openapi_function=openapi_function, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, OpenApiFunctions)


async def functions_convert_async(
    client: httpx.AsyncClient,
    *,
    openapi_function: str,
    access_token: Optional[str] = None,
) -> OpenApiFunctions:
    """Конвертация описание функции в формате OpenAPI в gigachat функцию"""
    kwargs = _get_functions_convert_kwargs(openapi_function=openapi_function, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, OpenApiFunctions)


def _get_ai_check_kwargs(
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


def ai_check_sync(
    client: httpx.Client,
    *,
    input_: str,
    model: str,
    access_token: Optional[str] = None,
) -> AICheckResult:
    kwargs = _get_ai_check_kwargs(input_=input_, model=model, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, AICheckResult)


async def ai_check_async(
    client: httpx.AsyncClient,
    *,
    input_: str,
    model: str,
    access_token: Optional[str] = None,
) -> AICheckResult:
    kwargs = _get_ai_check_kwargs(input_=input_, model=model, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, AICheckResult)


def _get_balance_kwargs(
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": "/balance",
        "headers": headers,
    }


def get_balance_sync(
    client: httpx.Client,
    *,
    access_token: Optional[str] = None,
) -> Balance:
    """Метод для получения баланса доступных для использования токенов.
    Только для клиентов с предоплатой иначе http 403"""
    kwargs = _get_balance_kwargs(access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Balance)


async def get_balance_async(
    client: httpx.AsyncClient,
    *,
    access_token: Optional[str] = None,
) -> Balance:
    """Метод для получения баланса доступных для использования токенов.
    Только для клиентов с предоплатой иначе http 403"""
    kwargs = _get_balance_kwargs(access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Balance)
