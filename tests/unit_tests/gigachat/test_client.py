import ssl

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from gigachat import GigaChat
from gigachat.client import (
    GigaChatAsyncClient,
    GigaChatSyncClient,
    _get_auth_kwargs,
    _get_kwargs,
    _logger,
)
from gigachat.settings import Settings

from ...utils import get_json

BASE_URL = "http://base_url"
AUTH_URL = "http://auth_url"

ACCESS_TOKEN = get_json("access_token.json")

CREDENTIALS = "NmIwNzhlODgtNDlkNC00ZjFmLTljMjMtYjFiZTZjMjVmNTRlOmU3NWJlNjVhLTk4YjAtNGY0Ni1iOWVhLTljMDkwZGE4YTk4MQ=="


def _make_ssl_context() -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    return context


def test__get_kwargs() -> None:
    settings = Settings(ca_bundle_file="ca.pem", cert_file="tls.pem", key_file="tls.key")
    assert _get_kwargs(settings)


def test__get_kwargs_ssl() -> None:
    context = _make_ssl_context()
    settings = Settings(ssl_context=context)
    assert _get_kwargs(settings)["verify"] == context


def test__get_auth_kwargs() -> None:
    settings = Settings(ca_bundle_file="ca.pem", cert_file="tls.pem", key_file="tls.key")
    assert _get_auth_kwargs(settings)


def test__get_auth_kwargs_ssl() -> None:
    context = _make_ssl_context()
    settings = Settings(ssl_context=context)
    assert _get_kwargs(settings)["verify"] == context


def test__unknown_kwargs(mocker: MockerFixture) -> None:
    spy = mocker.spy(_logger, "warning")

    GigaChatSyncClient(foo="bar")

    assert spy.call_count == 1


def test_get_token_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)

    model = GigaChat(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        credentials=CREDENTIALS,
    )
    access_token = model.get_token()

    assert model._access_token is not None
    assert model._access_token.access_token == ACCESS_TOKEN["access_token"]
    assert model._access_token.expires_at == ACCESS_TOKEN["expires_at"]
    assert access_token.access_token == ACCESS_TOKEN["access_token"]
    assert access_token.expires_at == ACCESS_TOKEN["expires_at"]


def test__update_token() -> None:
    with GigaChatSyncClient(base_url=BASE_URL) as client:
        client._update_token()


@pytest.mark.asyncio
async def test__aupdate_token() -> None:
    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        await client._aupdate_token()


@pytest.mark.asyncio
async def test_aget_token_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=ACCESS_TOKEN)

    model = GigaChat(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        credentials=CREDENTIALS,
    )
    access_token = await model.aget_token()

    assert model._access_token is not None
    assert model._access_token.access_token == ACCESS_TOKEN["access_token"]
    assert model._access_token.expires_at == ACCESS_TOKEN["expires_at"]
    assert access_token.access_token == ACCESS_TOKEN["access_token"]
    assert access_token.expires_at == ACCESS_TOKEN["expires_at"]
