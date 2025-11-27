from typing import List

import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import AICheckResult, Balance, Function, OpenApiFunctions, TokensCount
from gigachat.models.tools import BalanceValue

from ...utils import get_json

BASE_URL = "http://base_url"
TOKENS_COUNT_URL = f"{BASE_URL}/tokens/count"
BALANCE_URL = f"{BASE_URL}/balance"
CONVERT_FUNCTIONS_URL = f"{BASE_URL}/functions/convert"
AI_CHECK_URL = f"{BASE_URL}/ai/check"

TOKENS_COUNT = get_json("tokens_count.json")
BALANCE = get_json("balance.json")
CONVERT_FUNCTIONS = get_json("convert_functions.json")
AI_CHECK = get_json("ai_check.json")


def test_get_tokens_count(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.tokens_count(input_=["123"], model="GigaChat:latest")
    assert isinstance(response, List)
    for row in response:
        assert isinstance(row, TokensCount)


def test_balance(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, json=BALANCE)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        response = client.get_balance()
    assert isinstance(response, Balance)
    for row in response.balance:
        assert isinstance(row, BalanceValue)


def test_convert_functions(httpx_mock: HTTPXMock) -> None:
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


@pytest.mark.asyncio()
async def test_atokens_count(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.atokens_count(input_=["text"], model="GigaChat:latest")

    assert isinstance(response, List)
    for row in response:
        assert isinstance(row, TokensCount)


@pytest.mark.asyncio()
async def test_abalance(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, json=BALANCE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aget_balance()
    assert isinstance(response, Balance)
    for row in response.balance:
        assert isinstance(row, BalanceValue)


@pytest.mark.asyncio()
async def test_aconvert_functions(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CONVERT_FUNCTIONS_URL, json=CONVERT_FUNCTIONS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.aopenapi_function_convert(openapi_function="")
    assert isinstance(response, OpenApiFunctions)
    for row in response.functions:
        assert isinstance(row, Function)


@pytest.mark.asyncio()
async def test_acheck_ai(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AI_CHECK_URL, json=AI_CHECK)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        response = await client.acheck_ai(text="", model="")
    assert isinstance(response, AICheckResult)

