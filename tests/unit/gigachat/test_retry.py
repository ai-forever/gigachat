from gigachat.client import GigaChat
from gigachat.settings import Settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.max_retries == 0
    assert settings.retry_backoff_factor == 0.5
    assert settings.retry_on_status_codes == (429, 500, 502, 503, 504)


def test_settings_custom_values() -> None:
    settings = Settings(max_retries=3, retry_backoff_factor=1.0, retry_on_status_codes=(500, 503))
    assert settings.max_retries == 3
    assert settings.retry_backoff_factor == 1.0
    assert settings.retry_on_status_codes == (500, 503)


def test_client_retry_settings_init() -> None:
    client = GigaChat(credentials="test", max_retries=3, retry_backoff_factor=1.5, retry_on_status_codes=(500, 503))

    assert client._settings.max_retries == 3
    assert client._settings.retry_backoff_factor == 1.5
    assert client._settings.retry_on_status_codes == (500, 503)


def test_client_retry_settings_default() -> None:
    client = GigaChat(credentials="test")

    assert client._settings.max_retries == 0
    assert client._settings.retry_backoff_factor == 0.5
    assert client._settings.retry_on_status_codes == (429, 500, 502, 503, 504)
