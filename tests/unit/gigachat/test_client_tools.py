from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import (
    AICheckResult,
    Balance,
    FilterCheckRequest,
    FilterCheckResult,
    Function,
    Messages,
    MessagesRole,
    OpenApiFunctions,
)
from gigachat.models.tools import BalanceValue
from tests.constants import (
    AI_CHECK,
    AI_CHECK_URL,
    BALANCE,
    BALANCE_URL,
    BASE_URL,
    CONVERT_FUNCTIONS,
    CONVERT_FUNCTIONS_URL,
    FILTER_CHECK,
    FILTER_CHECK_URL,
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


def test_filter_check(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILTER_CHECK_URL, json=FILTER_CHECK)
    payload = FilterCheckRequest(messages=[Messages(role=MessagesRole.USER, content="text")])

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.filter_check(payload)

    assert isinstance(response, FilterCheckResult)


async def test_afilter_check(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=FILTER_CHECK_URL, json=FILTER_CHECK)
    payload = FilterCheckRequest(messages=[Messages(role=MessagesRole.USER, content="text")])

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.afilter_check(payload)

    assert isinstance(response, FilterCheckResult)
