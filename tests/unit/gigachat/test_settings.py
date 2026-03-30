import os
import ssl

import pytest
from pydantic import ValidationError

from gigachat.settings import AUTH_URL, BASE_URL, SCOPE, Settings


def test_defaults() -> None:
    settings = Settings()
    assert settings.base_url == BASE_URL
    assert settings.auth_url == AUTH_URL
    assert settings.scope == SCOPE
    assert settings.credentials is None
    assert settings.access_token is None
    assert settings.model is None
    assert settings.profanity_check is None
    assert settings.user is None
    assert settings.password is None
    assert settings.timeout == 30.0
    assert settings.verify_ssl_certs is True
    assert settings.ssl_context is None
    assert settings.ca_bundle_file is None
    assert settings.cert_file is None
    assert settings.key_file is None
    assert settings.key_file_password is None
    assert settings.flags is None
    assert settings.max_connections is None
    assert settings.max_retries == 0
    assert settings.retry_backoff_factor == 0.5
    assert settings.retry_on_status_codes == (429, 500, 502, 503, 504)


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    envs = {
        "GIGACHAT_BASE_URL": "http://custom-base",
        "GIGACHAT_AUTH_URL": "http://custom-auth",
        "GIGACHAT_CREDENTIALS": "custom-creds",
        "GIGACHAT_SCOPE": "custom-scope",
        "GIGACHAT_ACCESS_TOKEN": "custom-token",
        "GIGACHAT_MODEL": "custom-model",
        "GIGACHAT_PROFANITY_CHECK": "true",
        "GIGACHAT_USER": "custom-user",
        "GIGACHAT_PASSWORD": "custom-password",
        "GIGACHAT_TIMEOUT": "60.0",
        "GIGACHAT_VERIFY_SSL_CERTS": "false",
        "GIGACHAT_CA_BUNDLE_FILE": "ca.pem",
        "GIGACHAT_CERT_FILE": "cert.pem",
        "GIGACHAT_KEY_FILE": "key.pem",
        "GIGACHAT_KEY_FILE_PASSWORD": "key-pass",
        "GIGACHAT_MAX_CONNECTIONS": "100",
        "GIGACHAT_MAX_RETRIES": "5",
        "GIGACHAT_RETRY_BACKOFF_FACTOR": "1.5",
    }
    monkeypatch.setattr(os, "environ", envs)

    settings = Settings()

    assert settings.base_url == "http://custom-base"
    assert settings.auth_url == "http://custom-auth"
    assert settings.credentials is not None
    assert settings.credentials.get_secret_value() == "custom-creds"
    assert settings.scope == "custom-scope"
    assert settings.access_token is not None
    assert settings.access_token.get_secret_value() == "custom-token"
    assert settings.model == "custom-model"
    assert settings.profanity_check is True
    assert settings.user == "custom-user"
    assert settings.password is not None
    assert settings.password.get_secret_value() == "custom-password"
    assert settings.timeout == 60.0
    assert settings.verify_ssl_certs is False
    assert settings.ca_bundle_file == "ca.pem"
    assert settings.cert_file == "cert.pem"
    assert settings.key_file == "key.pem"
    assert settings.key_file_password is not None
    assert settings.key_file_password.get_secret_value() == "key-pass"
    assert settings.max_connections == 100
    assert settings.max_retries == 5
    assert settings.retry_backoff_factor == 1.5


def test_init_override() -> None:
    settings = Settings(
        base_url="http://init-base",
        max_retries=10,
        verify_ssl_certs=False,
    )
    assert settings.base_url == "http://init-base"
    assert settings.max_retries == 10
    assert settings.verify_ssl_certs is False


def test_validation_error() -> None:
    with pytest.raises(ValidationError):
        Settings(timeout="not-a-float")


def test_ssl_context() -> None:
    ctx = ssl.create_default_context()
    settings = Settings(ssl_context=ctx)
    assert settings.ssl_context is ctx


@pytest.mark.parametrize(
    ("env_val", "expected"),
    [
        ("1", True),
        ("True", True),
        ("true", True),
        ("0", False),
        ("False", False),
        ("false", False),
    ],
)
def test_bool_conversion(monkeypatch: pytest.MonkeyPatch, env_val: str, expected: bool) -> None:
    monkeypatch.setenv("GIGACHAT_VERIFY_SSL_CERTS", env_val)
    settings = Settings()
    assert settings.verify_ssl_certs is expected


def test_flags_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIGACHAT_FLAGS", '["flag1", "flag2"]')
    settings = Settings()
    assert settings.flags == ["flag1", "flag2"]


def test_retry_on_status_codes_override() -> None:
    settings = Settings(retry_on_status_codes=(500, 503))
    assert settings.retry_on_status_codes == (500, 503)
