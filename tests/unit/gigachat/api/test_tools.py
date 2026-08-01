import json

import httpx
from pytest_httpx import HTTPXMock

from gigachat.api.tools import (
    ai_check_async,
    ai_check_sync,
    functions_convert_async,
    functions_convert_sync,
    functions_validate_async,
    functions_validate_sync,
    get_balance_async,
    get_balance_sync,
    tokens_count_async,
    tokens_count_sync,
)
from gigachat.models.tools import (
    AICheckResult,
    Balance,
    CustomFunction,
    FunctionValidationResult,
    OpenApiFunctions,
    TokensCount,
)
from tests.constants import (
    AI_CHECK,
    AI_CHECK_URL,
    BALANCE,
    BALANCE_URL,
    BASE_URL,
    CONVERT_FUNCTIONS,
    CONVERT_FUNCTIONS_URL,
    TOKENS_COUNT,
    TOKENS_COUNT_URL,
)

FUNCTIONS_VALIDATE_URL = f"{BASE_URL}/functions/validate"
FUNCTION_SCHEMA = {
    "name": "send_sms",
    "description": "Send an SMS",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "minLength": 1, "pattern": "^.+$"},
            "contactId": {"type": "integer", "format": "int32", "minimum": 1},
        },
        "required": ["text", "contactId"],
        "additionalProperties": False,
    },
}
VALIDATION_RESULT = {
    "status": 200,
    "message": "Function is valid",
    "json_ai_rules_version": "1.0.5",
    "warnings": [{"description": "few_shot_examples are missing", "schema_location": "(root)"}],
}


def test_tokens_count_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    with httpx.Client(base_url=BASE_URL) as client:
        response = tokens_count_sync(client, input_=["text"], model="model")

    assert isinstance(response, list)
    assert all(isinstance(item, TokensCount) for item in response)


async def test_tokens_count_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await tokens_count_async(client, input_=["text"], model="model")

    assert isinstance(response, list)
    assert all(isinstance(item, TokensCount) for item in response)


def test_functions_convert_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CONVERT_FUNCTIONS_URL, json=CONVERT_FUNCTIONS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = functions_convert_sync(client, openapi_function="function")

    assert isinstance(response, OpenApiFunctions)


async def test_functions_convert_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CONVERT_FUNCTIONS_URL, json=CONVERT_FUNCTIONS)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await functions_convert_async(client, openapi_function="function")

    assert isinstance(response, OpenApiFunctions)


def test_functions_validate_sync_preserves_raw_json_schema(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FUNCTIONS_VALIDATE_URL, json=VALIDATION_RESULT)

    with httpx.Client(base_url=BASE_URL) as client:
        response = functions_validate_sync(client, function=FUNCTION_SCHEMA)

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.content) == FUNCTION_SCHEMA
    assert isinstance(response, FunctionValidationResult)


def test_functions_validate_sync_allows_server_to_validate_incomplete_raw_schema(httpx_mock: HTTPXMock) -> None:
    result = {
        "status": 200,
        "message": "Incorrect function syntax",
        "errors": [{"description": "name is required", "schema_location": "(root)"}],
    }
    httpx_mock.add_response(url=FUNCTIONS_VALIDATE_URL, json=result)

    with httpx.Client(base_url=BASE_URL) as client:
        response = functions_validate_sync(client, function={"parameters": {}})

    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"parameters": {}}
    assert response.errors is not None
    assert response.errors[0].description == "name is required"


async def test_functions_validate_async_accepts_typed_schema(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FUNCTIONS_VALIDATE_URL, json=VALIDATION_RESULT)
    function = CustomFunction.model_validate(FUNCTION_SCHEMA)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await functions_validate_async(client, function=function)

    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == FUNCTION_SCHEMA
    assert isinstance(response, FunctionValidationResult)


def test_ai_check_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AI_CHECK_URL, json=AI_CHECK, headers={"x-request-id": "request-1"})

    with httpx.Client(base_url=BASE_URL) as client:
        response = ai_check_sync(client, input_="text", model="model")

    assert isinstance(response, AICheckResult)
    assert response.x_headers is not None
    assert response.x_headers["x-request-id"] == "request-1"


async def test_ai_check_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AI_CHECK_URL, json=AI_CHECK)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await ai_check_async(client, input_="text", model="model")

    assert isinstance(response, AICheckResult)


def test_get_balance_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, json=BALANCE)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_balance_sync(client)

    assert isinstance(response, Balance)


async def test_get_balance_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, json=BALANCE)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_balance_async(client)

    assert isinstance(response, Balance)
