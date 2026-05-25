import warnings

import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.exceptions import ForbiddenError
from gigachat.models import Balance
from gigachat.models.tools import BalanceValue
from gigachat.resources.balance import BalanceAsyncResource, BalanceSyncResource
from tests.constants import BALANCE, BALANCE_URL, BASE_URL


def test_balance_resource_is_cached_property() -> None:
    client = GigaChatSyncClient()

    assert "balance" not in client.__dict__

    resource = client.balance

    assert resource is client.balance
    assert isinstance(resource, BalanceSyncResource)


async def test_a_balance_resource_is_cached_property() -> None:
    client = GigaChatAsyncClient()

    assert "a_balance" not in client.__dict__

    resource = client.a_balance

    assert resource is client.a_balance
    assert isinstance(resource, BalanceAsyncResource)


def test_balance_get_without_warning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, json=BALANCE)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.balance.get()

    assert isinstance(response, Balance)
    for row in response.balance:
        assert isinstance(row, BalanceValue)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_get_balance_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, json=BALANCE)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.balance\.get\(\)"):
            response = client.get_balance()

    assert isinstance(response, Balance)
    for row in response.balance:
        assert isinstance(row, BalanceValue)


def test_balance_get_preserves_forbidden_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, status_code=403, json={"message": "Forbidden"})

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.raises(ForbiddenError):
            client.balance.get()


async def test_a_balance_get_without_warning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, json=BALANCE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_balance.get()

    assert isinstance(response, Balance)
    for row in response.balance:
        assert isinstance(row, BalanceValue)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_aget_balance_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=BALANCE_URL, json=BALANCE)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_balance\.get\(\)"):
            response = await client.aget_balance()

    assert isinstance(response, Balance)
    for row in response.balance:
        assert isinstance(row, BalanceValue)
