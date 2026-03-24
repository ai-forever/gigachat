import logging

import pytest

from gigachat.client import GigaChat, GigaChatAsyncClient, GigaChatSyncClient


def test_gigachat_constructor_explicit_params() -> None:
    """Test that GigaChat constructor accepts all explicit parameters."""
    client = GigaChat(
        base_url="https://example.com",
        auth_url="https://auth.example.com",
        credentials="test_credentials",
        scope="test_scope",
        access_token="test_token",
        model="test_model",
        profanity_check=True,
        user="test_user",
        password="test_password",
        timeout=60.0,
        verify_ssl_certs=False,
        ca_bundle_file="ca.pem",
        cert_file="cert.pem",
        key_file="key.pem",
        key_file_password="key_password",
        flags=["test_flag"],
        max_connections=10,
        max_retries=3,
        retry_backoff_factor=0.1,
        retry_on_status_codes=(500, 502),
    )

    # Verify settings were populated correctly
    assert client._settings.base_url == "https://example.com"
    assert client._settings.auth_url == "https://auth.example.com"
    assert client._settings.credentials is not None
    assert client._settings.credentials.get_secret_value() == "test_credentials"
    assert client._settings.scope == "test_scope"
    assert client._settings.access_token is not None
    assert client._settings.access_token.get_secret_value() == "test_token"
    assert client._settings.model == "test_model"
    assert client._settings.profanity_check is True
    assert client._settings.user == "test_user"
    assert client._settings.password is not None
    assert client._settings.password.get_secret_value() == "test_password"
    assert client._settings.timeout == 60.0
    assert client._settings.verify_ssl_certs is False
    assert client._settings.ca_bundle_file == "ca.pem"
    assert client._settings.cert_file == "cert.pem"
    assert client._settings.key_file == "key.pem"
    assert client._settings.key_file_password is not None
    assert client._settings.key_file_password.get_secret_value() == "key_password"
    assert client._settings.flags == ["test_flag"]
    assert client._settings.max_connections == 10
    assert client._settings.max_retries == 3
    assert client._settings.retry_backoff_factor == 0.1
    assert client._settings.retry_on_status_codes == (500, 502)


def test_gigachat_constructor_unknown_kwargs(caplog: pytest.LogCaptureFixture) -> None:
    """Test that GigaChat constructor logs warning for unknown kwargs."""
    with caplog.at_level(logging.WARNING):
        client = GigaChat(
            credentials="test_credentials",
            unknown_param="test_value",
            another_unknown=123,
        )

    # Verify warning was logged
    assert "GigaChat: unknown kwargs - {'unknown_param': 'test_value', 'another_unknown': 123}" in caplog.text

    # Verify known param was still processed
    assert client._settings.credentials is not None
    assert client._settings.credentials.get_secret_value() == "test_credentials"


def test_gigachat_sync_constructor_explicit_params() -> None:
    """Test that GigaChatSyncClient constructor accepts explicit parameters."""
    client = GigaChatSyncClient(base_url="https://sync.example.com")
    assert client._settings.base_url == "https://sync.example.com"


def test_gigachat_async_constructor_explicit_params() -> None:
    """Test that GigaChatAsyncClient constructor accepts explicit parameters."""
    client = GigaChatAsyncClient(base_url="https://async.example.com")
    assert client._settings.base_url == "https://async.example.com"
