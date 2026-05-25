import json
import warnings

import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GIGACHAT_MODEL, GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import TokensCount
from gigachat.resources.tokens import TokensAsyncResource, TokensSyncResource
from tests.constants import BASE_URL, TOKENS_COUNT, TOKENS_COUNT_URL


def test_tokens_resource_is_cached_property() -> None:
    client = GigaChatSyncClient()

    assert "tokens" not in client.__dict__

    resource = client.tokens

    assert resource is client.tokens
    assert isinstance(resource, TokensSyncResource)


async def test_a_tokens_resource_is_cached_property() -> None:
    client = GigaChatAsyncClient()

    assert "a_tokens" not in client.__dict__

    resource = client.a_tokens

    assert resource is client.a_tokens
    assert isinstance(resource, TokensAsyncResource)


def test_tokens_count_resource_uses_settings_model_without_warning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    with GigaChatSyncClient(base_url=BASE_URL, model="settings-model") as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.tokens.count(["text"])

    request_body = json.loads(httpx_mock.get_requests()[0].content)

    assert isinstance(response, list)
    assert all(isinstance(item, TokensCount) for item in response)
    assert request_body == {"input": ["text"], "model": "settings-model"}
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_tokens_count_resource_uses_default_model_without_warning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.tokens.count(["text"])

    request_body = json.loads(httpx_mock.get_requests()[0].content)

    assert isinstance(response, list)
    assert all(isinstance(item, TokensCount) for item in response)
    assert request_body == {"input": ["text"], "model": GIGACHAT_MODEL}
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_tokens_count_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    with GigaChatSyncClient(base_url=BASE_URL, model="settings-model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.tokens\.count\(\.\.\.\)"):
            response = client.tokens_count(["text"])

    request_body = json.loads(httpx_mock.get_requests()[0].content)

    assert isinstance(response, list)
    assert all(isinstance(item, TokensCount) for item in response)
    assert request_body == {"input": ["text"], "model": "settings-model"}


async def test_a_tokens_count_resource_uses_settings_model_without_warning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    async with GigaChatAsyncClient(base_url=BASE_URL, model="settings-model") as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_tokens.count(["text"])

    request_body = json.loads(httpx_mock.get_requests()[0].content)

    assert isinstance(response, list)
    assert all(isinstance(item, TokensCount) for item in response)
    assert request_body == {"input": ["text"], "model": "settings-model"}
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_a_tokens_count_resource_uses_default_model_without_warning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_tokens.count(["text"])

    request_body = json.loads(httpx_mock.get_requests()[0].content)

    assert isinstance(response, list)
    assert all(isinstance(item, TokensCount) for item in response)
    assert request_body == {"input": ["text"], "model": GIGACHAT_MODEL}
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_atokens_count_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKENS_COUNT_URL, json=TOKENS_COUNT)

    async with GigaChatAsyncClient(base_url=BASE_URL, model="settings-model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_tokens\.count\(\.\.\.\)"):
            response = await client.atokens_count(["text"])

    request_body = json.loads(httpx_mock.get_requests()[0].content)

    assert isinstance(response, list)
    assert all(isinstance(item, TokensCount) for item in response)
    assert request_body == {"input": ["text"], "model": "settings-model"}
