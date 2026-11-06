import json
from http import HTTPStatus
from typing import Any

import httpx2 as httpx
from pydantic import ValidationError

from gigachat._core.execution import request_async, request_sync
from gigachat.api.utils import build_headers, build_x_headers, execute_request_async, execute_request_sync
from gigachat.exceptions import APIResponseValidationError, AuthenticationError, ResponseError
from gigachat.models.tools import (
    AICheckResult,
    Balance,
    FunctionValidationResult,
    GeneratedContent,
    OpenApiFunctions,
    RankedFunctions,
    RerankResponse,
    TokensCount,
)


def _get_tokens_count_kwargs(
    *,
    input_: str | list[str],
    model: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/json"

    json_data = {"model": model, "input": input_}

    return {
        "method": "POST",
        "url": "/tokens/count",
        "headers": headers,
        "content": json.dumps(json_data, ensure_ascii=False),
    }


def _build_tokens_count_response(response: httpx.Response) -> list[TokensCount]:
    if response.status_code == HTTPStatus.OK:
        try:
            payload = response.json()
            rows = [payload] if isinstance(payload, dict) else payload
            if not isinstance(rows, list):
                raise ValueError("Expected a token count object or array")
            return [TokensCount.model_validate({**row, "x_headers": build_x_headers(response)}) for row in rows]
        except (ValidationError, ValueError, TypeError) as exc:
            raise APIResponseValidationError(
                "Invalid token count response", request_id=response.headers.get("x-request-id")
            ) from exc
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def tokens_count_sync(
    client: httpx.Client,
    *,
    input_: str | list[str],
    model: str,
    access_token: str | None = None,
) -> list[TokensCount]:
    """Count tokens in input text."""
    kwargs = _get_tokens_count_kwargs(input_=input_, model=model, access_token=access_token)
    response = request_sync(client, **kwargs)
    return _build_tokens_count_response(response)


async def tokens_count_async(
    client: httpx.AsyncClient,
    *,
    input_: str | list[str],
    model: str,
    access_token: str | None = None,
) -> list[TokensCount]:
    """Count tokens in input text."""
    kwargs = _get_tokens_count_kwargs(input_=input_, model=model, access_token=access_token)
    response = await request_async(client, **kwargs)
    return _build_tokens_count_response(response)


def _get_functions_convert_kwargs(
    *,
    openapi_function: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/x-yaml"

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
    access_token: str | None = None,
) -> OpenApiFunctions:
    """Convert OpenAPI function definition to GigaChat format."""
    kwargs = _get_functions_convert_kwargs(openapi_function=openapi_function, access_token=access_token)
    return execute_request_sync(client, kwargs, OpenApiFunctions)


async def functions_convert_async(
    client: httpx.AsyncClient,
    *,
    openapi_function: str,
    access_token: str | None = None,
) -> OpenApiFunctions:
    """Convert OpenAPI function definition to GigaChat format."""
    kwargs = _get_functions_convert_kwargs(openapi_function=openapi_function, access_token=access_token)
    return await execute_request_async(client, kwargs, OpenApiFunctions)


def _get_ai_check_kwargs(
    *,
    input_: str,
    model: str,
    access_token: str | None = None,
) -> dict[str, Any]:
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
    access_token: str | None = None,
) -> AICheckResult:
    """Check text for AI-generated content."""
    kwargs = _get_ai_check_kwargs(input_=input_, model=model, access_token=access_token)
    return execute_request_sync(client, kwargs, AICheckResult)


async def ai_check_async(
    client: httpx.AsyncClient,
    *,
    input_: str,
    model: str,
    access_token: str | None = None,
) -> AICheckResult:
    """Check text for AI-generated content."""
    kwargs = _get_ai_check_kwargs(input_=input_, model=model, access_token=access_token)
    return await execute_request_async(client, kwargs, AICheckResult)


def _get_balance_kwargs(
    *,
    access_token: str | None = None,
) -> dict[str, Any]:
    """Return keyword arguments for get_balance request."""
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": "/balance",
        "headers": headers,
    }


def get_balance_sync(
    client: httpx.Client,
    *,
    access_token: str | None = None,
) -> Balance:
    """
    Return the balance of available tokens.

    Only for prepaid clients, otherwise HTTP 403.
    """
    kwargs = _get_balance_kwargs(access_token=access_token)
    return execute_request_sync(client, kwargs, Balance)


async def get_balance_async(
    client: httpx.AsyncClient,
    *,
    access_token: str | None = None,
) -> Balance:
    """
    Return the balance of available tokens.

    Only for prepaid clients, otherwise HTTP 403.
    """
    kwargs = _get_balance_kwargs(access_token=access_token)
    return await execute_request_async(client, kwargs, Balance)


def _validate_function_kwargs(function: dict[str, Any] | str | bytes, access_token: str | None) -> dict[str, Any]:
    headers = build_headers(access_token)
    if isinstance(function, dict):
        headers["Content-Type"] = "application/json"
        return {"method": "POST", "url": "/functions/validate", "headers": headers, "json": function}
    headers["Content-Type"] = "application/x-yaml"
    return {"method": "POST", "url": "/functions/validate", "headers": headers, "content": function}


def functions_validate_sync(
    client: httpx.Client, *, function: dict[str, Any] | str | bytes, access_token: str | None = None
) -> FunctionValidationResult:
    """Validate a function object or raw OpenAPI YAML."""
    return execute_request_sync(client, _validate_function_kwargs(function, access_token), FunctionValidationResult)


async def functions_validate_async(
    client: httpx.AsyncClient, *, function: dict[str, Any] | str | bytes, access_token: str | None = None
) -> FunctionValidationResult:
    """Validate a function object or raw OpenAPI YAML."""
    return await execute_request_async(
        client, _validate_function_kwargs(function, access_token), FunctionValidationResult
    )


def functions_generate_sync(
    client: httpx.Client, *, model: str, input_: str, access_token: str | None = None
) -> GeneratedContent:
    """Call /functions/generate."""
    kwargs = _get_functions_generate_kwargs(model=model, input_=input_, access_token=access_token)
    return execute_request_sync(client, kwargs, GeneratedContent)


async def functions_generate_async(
    client: httpx.AsyncClient, *, model: str, input_: str, access_token: str | None = None
) -> GeneratedContent:
    """Call /functions/generate."""
    kwargs = _get_functions_generate_kwargs(model=model, input_=input_, access_token=access_token)
    return await execute_request_async(client, kwargs, GeneratedContent)


def instructions_generate_sync(
    client: httpx.Client, *, model: str, input_: str, access_token: str | None = None
) -> GeneratedContent:
    """Call /instructions/generate."""
    kwargs = _get_instructions_generate_kwargs(model=model, input_=input_, access_token=access_token)
    return execute_request_sync(client, kwargs, GeneratedContent)


async def instructions_generate_async(
    client: httpx.AsyncClient, *, model: str, input_: str, access_token: str | None = None
) -> GeneratedContent:
    """Call /instructions/generate."""
    kwargs = _get_instructions_generate_kwargs(model=model, input_=input_, access_token=access_token)
    return await execute_request_async(client, kwargs, GeneratedContent)


def functions_rank_sync(
    client: httpx.Client,
    *,
    messages: list[dict[str, Any]],
    functions: list[dict[str, Any]],
    options: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> RankedFunctions:
    """Call /functions/rank."""
    kwargs = _get_functions_rank_kwargs(
        messages=messages, functions=functions, options=options, access_token=access_token
    )
    return execute_request_sync(client, kwargs, RankedFunctions)


async def functions_rank_async(
    client: httpx.AsyncClient,
    *,
    messages: list[dict[str, Any]],
    functions: list[dict[str, Any]],
    options: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> RankedFunctions:
    """Call /functions/rank."""
    kwargs = _get_functions_rank_kwargs(
        messages=messages, functions=functions, options=options, access_token=access_token
    )
    return await execute_request_async(client, kwargs, RankedFunctions)


def rerank_sync(
    client: httpx.Client,
    *,
    model: str,
    input_: list[dict[str, Any]],
    options: dict[str, Any] | None = None,
    include_documents: bool | None = None,
    access_token: str | None = None,
) -> RerankResponse:
    """Call /rerank."""
    kwargs = _get_rerank_kwargs(
        model=model, input_=input_, options=options, include_documents=include_documents, access_token=access_token
    )
    return execute_request_sync(client, kwargs, RerankResponse)


async def rerank_async(
    client: httpx.AsyncClient,
    *,
    model: str,
    input_: list[dict[str, Any]],
    options: dict[str, Any] | None = None,
    include_documents: bool | None = None,
    access_token: str | None = None,
) -> RerankResponse:
    """Call /rerank."""
    kwargs = _get_rerank_kwargs(
        model=model, input_=input_, options=options, include_documents=include_documents, access_token=access_token
    )
    return await execute_request_async(client, kwargs, RerankResponse)


def _get_functions_generate_kwargs(*, model: str, input_: str, access_token: str | None) -> dict[str, Any]:
    return {
        "method": "POST",
        "url": "/functions/generate",
        "headers": build_headers(access_token),
        "json": {"model": model, "input": input_},
    }


def _get_instructions_generate_kwargs(*, model: str, input_: str, access_token: str | None) -> dict[str, Any]:
    return {
        "method": "POST",
        "url": "/instructions/generate",
        "headers": build_headers(access_token),
        "json": {"model": model, "input": input_},
    }


def _get_functions_rank_kwargs(
    *,
    messages: list[dict[str, Any]],
    functions: list[dict[str, Any]],
    options: dict[str, Any] | None,
    access_token: str | None,
) -> dict[str, Any]:
    return {
        "method": "POST",
        "url": "/functions/rank",
        "headers": build_headers(access_token),
        "json": {"messages": messages, "functions": functions, **({"options": options} if options is not None else {})},
    }


def _get_rerank_kwargs(
    *,
    model: str,
    input_: list[dict[str, Any]],
    options: dict[str, Any] | None,
    include_documents: bool | None,
    access_token: str | None,
) -> dict[str, Any]:
    return {
        "method": "POST",
        "url": "/rerank",
        "headers": build_headers(access_token),
        "json": {
            "model": model,
            "input": input_,
            **({"options": options} if options is not None else {}),
            **({"include_documents": include_documents} if include_documents is not None else {}),
        },
    }
