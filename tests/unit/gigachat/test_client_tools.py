from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import AICheckResult, Balance, Function, FunctionValidationResult, OpenApiFunctions
from gigachat.models.tools import BalanceValue
from tests.constants import (
    AI_CHECK,
    AI_CHECK_URL,
    BALANCE,
    BALANCE_URL,
    BASE_URL,
    CONVERT_FUNCTIONS,
    CONVERT_FUNCTIONS_URL,
    FUNCTION_VALIDATION,
    VALIDATE_FUNCTION_URL,
)


def test_get_balance(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, json=BALANCE)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.get_balance()
    assert isinstance(response, Balance)
    for row in response.balance:
        assert isinstance(row, BalanceValue)


def test_openapi_function_convert(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CONVERT_FUNCTIONS_URL, json=CONVERT_FUNCTIONS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.openapi_function_convert(openapi_function="")
    assert isinstance(response, OpenApiFunctions)
    for row in response.functions:
        assert isinstance(row, Function)


def test_check_ai(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AI_CHECK_URL, json=AI_CHECK)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.check_ai(text="", model="")
    assert isinstance(response, AICheckResult)


def test_validate_function(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=VALIDATE_FUNCTION_URL, json=FUNCTION_VALIDATION)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.validate_function(
            Function.model_validate(
                {
                    "name": "weather_forecast",
                    "parameters": {"type": "object", "properties": {"location": {"type": "string"}}},
                }
            )
        )
    assert isinstance(response, FunctionValidationResult)


async def test_aget_balance(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, json=BALANCE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_balance()
    assert isinstance(response, Balance)
    for row in response.balance:
        assert isinstance(row, BalanceValue)


async def test_aopenapi_function_convert(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CONVERT_FUNCTIONS_URL, json=CONVERT_FUNCTIONS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aopenapi_function_convert(openapi_function="")
    assert isinstance(response, OpenApiFunctions)
    for row in response.functions:
        assert isinstance(row, Function)


async def test_acheck_ai(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AI_CHECK_URL, json=AI_CHECK)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.acheck_ai(text="", model="")
    assert isinstance(response, AICheckResult)


async def test_avalidate_function(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=VALIDATE_FUNCTION_URL, json=FUNCTION_VALIDATION)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.avalidate_function(
            {
                "name": "weather_forecast",
                "parameters": {"type": "object", "properties": {"location": {"type": "string"}}},
            }
        )
    assert isinstance(response, FunctionValidationResult)
