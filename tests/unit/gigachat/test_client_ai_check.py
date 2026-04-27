import warnings

import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import AICheckResult
from gigachat.resources.ai_check import AICheckAsyncResource, AICheckSyncResource
from tests.constants import AI_CHECK, AI_CHECK_URL, BASE_URL


def test_ai_check_resource_is_cached_property() -> None:
    client = GigaChatSyncClient()

    assert "ai_check" not in client.__dict__

    resource = client.ai_check

    assert resource is client.ai_check
    assert isinstance(resource, AICheckSyncResource)


async def test_a_ai_check_resource_is_cached_property() -> None:
    client = GigaChatAsyncClient()

    assert "a_ai_check" not in client.__dict__

    resource = client.a_ai_check

    assert resource is client.a_ai_check
    assert isinstance(resource, AICheckAsyncResource)


def test_ai_check_check_without_warning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AI_CHECK_URL, json=AI_CHECK)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.ai_check.check(text="", model="")

    assert isinstance(response, AICheckResult)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_check_ai_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AI_CHECK_URL, json=AI_CHECK)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.ai_check\.check\(\.\.\.\)"):
            response = client.check_ai(text="", model="")

    assert isinstance(response, AICheckResult)


async def test_a_ai_check_check_without_warning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AI_CHECK_URL, json=AI_CHECK)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_ai_check.check(text="", model="")

    assert isinstance(response, AICheckResult)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_acheck_ai_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AI_CHECK_URL, json=AI_CHECK)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_ai_check\.check\(\.\.\.\)"):
            response = await client.acheck_ai(text="", model="")

    assert isinstance(response, AICheckResult)
