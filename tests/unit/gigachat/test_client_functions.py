import warnings

import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models import Function, OpenApiFunctions
from gigachat.resources.functions import FunctionsAsyncResource, FunctionsSyncResource
from tests.constants import BASE_URL, CONVERT_FUNCTIONS, CONVERT_FUNCTIONS_URL


def test_functions_resource_is_cached_property() -> None:
    client = GigaChatSyncClient()

    assert "functions" not in client.__dict__

    resource = client.functions

    assert resource is client.functions
    assert isinstance(resource, FunctionsSyncResource)


async def test_a_functions_resource_is_cached_property() -> None:
    client = GigaChatAsyncClient()

    assert "a_functions" not in client.__dict__

    resource = client.a_functions

    assert resource is client.a_functions
    assert isinstance(resource, FunctionsAsyncResource)


def test_functions_convert_openapi_without_warning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CONVERT_FUNCTIONS_URL, json=CONVERT_FUNCTIONS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.functions.convert_openapi(openapi_function="")

    assert isinstance(response, OpenApiFunctions)
    for row in response.functions:
        assert isinstance(row, Function)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_openapi_function_convert_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CONVERT_FUNCTIONS_URL, json=CONVERT_FUNCTIONS)

    with GigaChatSyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.functions\.convert_openapi\(\.\.\.\)"):
            response = client.openapi_function_convert(openapi_function="")

    assert isinstance(response, OpenApiFunctions)
    for row in response.functions:
        assert isinstance(row, Function)


async def test_a_functions_convert_openapi_without_warning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CONVERT_FUNCTIONS_URL, json=CONVERT_FUNCTIONS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.a_functions.convert_openapi(openapi_function="")

    assert isinstance(response, OpenApiFunctions)
    for row in response.functions:
        assert isinstance(row, Function)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_aopenapi_function_convert_deprecated_shim(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CONVERT_FUNCTIONS_URL, json=CONVERT_FUNCTIONS)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.a_functions\.convert_openapi\(\.\.\.\)"):
            response = await client.aopenapi_function_convert(openapi_function="")

    assert isinstance(response, OpenApiFunctions)
    for row in response.functions:
        assert isinstance(row, Function)
