from typing import AsyncIterator, Iterator
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from gigachat.client import GigaChat
from gigachat.exceptions import RateLimitError, ResponseError, ServerError
from gigachat.retry import (
    _awith_retry,
    _awith_retry_stream,
    _calculate_backoff,
    _get_retry_settings,
    _with_retry,
    _with_retry_stream,
)
from gigachat.settings import Settings

# --- Settings Tests ---


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


# --- Client Init Tests ---


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


# --- Retry Helper Tests ---


class MockClient:
    def __init__(self) -> None:
        self._settings = Settings()


class MockSubClient:
    def __init__(self, base_client: MockClient) -> None:
        self._base_client = base_client


class MockInvalidClient:
    pass


def test_get_retry_settings_from_client() -> None:
    client = MockClient()
    settings = _get_retry_settings(client)
    assert isinstance(settings, Settings)
    assert settings.max_retries == 0


def test_get_retry_settings_from_sub_client() -> None:
    client = MockClient()
    sub_client = MockSubClient(client)
    settings = _get_retry_settings(sub_client)
    assert isinstance(settings, Settings)
    assert settings.max_retries == 0


def test_get_retry_settings_value_error() -> None:
    client = MockInvalidClient()
    with pytest.raises(ValueError, match="Cannot resolve settings from"):
        _get_retry_settings(client)


# --- Backoff Calculation Tests ---


def test_backoff_rate_limit_retry_after() -> None:
    # Create a mock exception that behaves like RateLimitError with retry_after
    exc = Mock(spec=RateLimitError)
    exc.retry_after = 12.5

    delay = _calculate_backoff(attempt=0, factor=0.5, exception=exc)
    assert delay == 12.5


def test_backoff_exponential() -> None:
    exc = Exception("test")

    # attempt 0: 0.5 * 2^0 + jitter(0-0.5) => 0.5 to 1.0
    delay0 = _calculate_backoff(attempt=0, factor=0.5, exception=exc)
    assert 0.5 <= delay0 <= 1.0

    # attempt 1: 0.5 * 2^1 + jitter(0-0.5) => 1.0 to 1.5
    delay1 = _calculate_backoff(attempt=1, factor=0.5, exception=exc)
    assert 1.0 <= delay1 <= 1.5

    # attempt 2: 0.5 * 2^2 + jitter(0-0.5) => 2.0 to 2.5
    delay2 = _calculate_backoff(attempt=2, factor=0.5, exception=exc)
    assert 2.0 <= delay2 <= 2.5


def test_backoff_cap() -> None:
    exc = Exception("test")
    # attempt 100: huge number, should be capped at 60
    delay = _calculate_backoff(attempt=100, factor=0.5, exception=exc)
    assert delay == 60.0


# --- Sync Retry Decorator Tests ---


class MockSyncClient:
    def __init__(self, max_retries: int = 0) -> None:
        self._settings = Settings(max_retries=max_retries)
        self.call_count = 0

    @_with_retry
    def request(self, *args, **kwargs):
        self.call_count += 1
        return "success"

    @_with_retry
    def failing_request(self, error):
        self.call_count += 1
        raise error


@patch("gigachat.retry.time.sleep")
def test_sync_retry_success(mock_sleep) -> None:
    client = MockSyncClient(max_retries=3)
    result = client.request()
    assert result == "success"
    assert client.call_count == 1
    mock_sleep.assert_not_called()


@patch("gigachat.retry.time.sleep")
def test_sync_retry_rate_limit(mock_sleep) -> None:
    client = MockSyncClient(max_retries=2)
    error = RateLimitError(url="test", status_code=429, content=b"", headers=None)

    # Mock side effect: fail twice, then succeed
    call_count = 0

    def side_effect(self, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise error
        return "success"

    # Manually decorate the side effect function
    decorated = _with_retry(side_effect)

    # Call with client as 'self'
    result = decorated(client)

    assert result == "success"
    assert call_count == 3
    assert mock_sleep.call_count == 2


@patch("gigachat.retry.time.sleep")
def test_sync_retry_max_retries_exceeded(mock_sleep) -> None:
    client = MockSyncClient(max_retries=2)
    error = ServerError(url="test", status_code=500, content=b"", headers=None)

    with pytest.raises(ServerError):
        client.failing_request(error)

    assert client.call_count == 3  # Initial + 2 retries
    assert mock_sleep.call_count == 2


@patch("gigachat.retry.time.sleep")
def test_sync_retry_non_retryable_error(mock_sleep) -> None:
    client = MockSyncClient(max_retries=3)
    # 400 Bad Request is not retryable by default
    error = ResponseError(url="test", status_code=400, content=b"", headers=None)

    with pytest.raises(ResponseError):
        client.failing_request(error)

    assert client.call_count == 1
    mock_sleep.assert_not_called()


@patch("gigachat.retry.time.sleep")
def test_sync_retry_transport_error(mock_sleep) -> None:
    client = MockSyncClient(max_retries=1)
    error = httpx.TransportError("Connection failed")

    with pytest.raises(httpx.TransportError):
        client.failing_request(error)

    assert client.call_count == 2
    assert mock_sleep.call_count == 1


# --- Sync Retry Stream Decorator Tests ---


class MockSyncStreamClient:
    def __init__(self, max_retries: int = 0) -> None:
        self._settings = Settings(max_retries=max_retries)
        self.call_count = 0

    @_with_retry_stream
    def stream(self, *args, **kwargs) -> Iterator[str]:
        self.call_count += 1
        yield "chunk1"
        yield "chunk2"

    @_with_retry_stream
    def failing_stream(self, error):
        self.call_count += 1
        raise error
        yield "chunk1"  # unreachable


@patch("gigachat.retry.time.sleep")
def test_sync_stream_retry_success(mock_sleep) -> None:
    client = MockSyncStreamClient(max_retries=3)
    result = list(client.stream())
    assert result == ["chunk1", "chunk2"]
    assert client.call_count == 1
    mock_sleep.assert_not_called()


@patch("gigachat.retry.time.sleep")
def test_sync_stream_retry_failure(mock_sleep) -> None:
    client = MockSyncStreamClient(max_retries=2)
    error = RateLimitError(url="test", status_code=429, content=b"", headers=None)

    # Redefine failing_stream to simulate retry success
    call_count = 0

    def side_effect(self, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise error
        yield "chunk1"

    decorated = _with_retry_stream(side_effect)

    result = list(decorated(client))

    assert result == ["chunk1"]
    assert call_count == 3
    assert mock_sleep.call_count == 2


# --- Async Retry Decorator Tests ---


class MockAsyncClient:
    def __init__(self, max_retries: int = 0) -> None:
        self._settings = Settings(max_retries=max_retries)
        self.call_count = 0

    @_awith_retry
    async def request(self, *args, **kwargs):
        self.call_count += 1
        return "success"

    @_awith_retry
    async def failing_request(self, error):
        self.call_count += 1
        raise error


@pytest.mark.asyncio()
async def test_async_retry_success() -> None:
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        client = MockAsyncClient(max_retries=3)
        result = await client.request()
        assert result == "success"
        assert client.call_count == 1
        mock_sleep.assert_not_called()


@pytest.mark.asyncio()
async def test_async_retry_failure() -> None:
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        client = MockAsyncClient(max_retries=2)
        error = RateLimitError(url="test", status_code=429, content=b"", headers=None)

        call_count = 0

        async def side_effect(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise error
            return "success"

        decorated = _awith_retry(side_effect)

        result = await decorated(client)

        assert result == "success"
        assert call_count == 3
        assert mock_sleep.call_count == 2


# --- Async Retry Stream Decorator Tests ---


class MockAsyncStreamClient:
    def __init__(self, max_retries: int = 0) -> None:
        self._settings = Settings(max_retries=max_retries)
        self.call_count = 0

    @_awith_retry_stream
    async def stream(self, *args, **kwargs) -> AsyncIterator[str]:
        self.call_count += 1
        yield "chunk1"
        yield "chunk2"

    @_awith_retry_stream
    async def failing_stream(self, error):
        self.call_count += 1
        raise error
        yield "chunk1"  # unreachable


@pytest.mark.asyncio()
async def test_async_stream_retry_success() -> None:
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        client = MockAsyncStreamClient(max_retries=3)
        result = [chunk async for chunk in client.stream()]
        assert result == ["chunk1", "chunk2"]
        assert client.call_count == 1
        mock_sleep.assert_not_called()


@pytest.mark.asyncio()
async def test_async_stream_retry_failure() -> None:
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        client = MockAsyncStreamClient(max_retries=2)
        error = RateLimitError(url="test", status_code=429, content=b"", headers=None)

        call_count = 0

        async def side_effect(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise error
            yield "chunk1"

        decorated = _awith_retry_stream(side_effect)

        result = [chunk async for chunk in decorated(client)]

        assert result == ["chunk1"]
        assert call_count == 3
        assert mock_sleep.call_count == 2
