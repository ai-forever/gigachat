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
    VALIDATE_FUNCTION,
    VALIDATE_FUNCTION_URL,
)


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


def test_functions_validate_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=VALIDATE_FUNCTION_URL, json=VALIDATE_FUNCTION)

    with httpx.Client(base_url=BASE_URL) as client:
        response = functions_validate_sync(
            client,
            function=CustomFunction(name="weather_forecast", parameters={"type": "object", "properties": {}}),
        )

    assert isinstance(response, FunctionValidationResult)


def test_functions_validate_sync_with_dict(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=VALIDATE_FUNCTION_URL, json=VALIDATE_FUNCTION)

    with httpx.Client(base_url=BASE_URL) as client:
        response = functions_validate_sync(
            client,
            function={"name": "weather_forecast", "parameters": {"type": "object", "properties": {}}},
        )

    assert isinstance(response, FunctionValidationResult)


async def test_functions_validate_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=VALIDATE_FUNCTION_URL, json=VALIDATE_FUNCTION)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await functions_validate_async(
            client,
            function=CustomFunction(name="weather_forecast", parameters={"type": "object", "properties": {}}),
        )

    assert isinstance(response, FunctionValidationResult)


async def test_functions_validate_async_with_dict(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=VALIDATE_FUNCTION_URL, json=VALIDATE_FUNCTION)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await functions_validate_async(
            client,
            function={"name": "weather_forecast", "parameters": {"type": "object", "properties": {}}},
        )

    assert isinstance(response, FunctionValidationResult)


def test_ai_check_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AI_CHECK_URL, json=AI_CHECK)

    with httpx.Client(base_url=BASE_URL) as client:
        response = ai_check_sync(client, input_="text", model="model")

    assert isinstance(response, AICheckResult)


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
