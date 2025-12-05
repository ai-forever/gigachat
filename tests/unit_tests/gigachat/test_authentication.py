from typing import Any, AsyncIterator, Iterator
from unittest.mock import AsyncMock, Mock

from gigachat.authentication import (
    _awith_auth,
    _awith_auth_stream,
    _with_auth,
    _with_auth_stream,
)
from gigachat.exceptions import AuthenticationError


class MockAuthClient:
    def __init__(self, use_auth: bool = True, token_valid: bool = True) -> None:
        self._use_auth_val = use_auth
        self._token_valid = token_valid
        self._reset_token_mock = Mock()
        self._update_token_mock = Mock()

    @property
    def _use_auth(self) -> bool:
        return self._use_auth_val

    def _is_token_usable(self) -> bool:
        return self._token_valid

    def _reset_token(self) -> None:
        self._reset_token_mock()
        self._token_valid = False

    def _update_token(self) -> None:
        self._update_token_mock()
        self._token_valid = True


class MockAsyncAuthClient:
    def __init__(self, use_auth: bool = True, token_valid: bool = True) -> None:
        self._use_auth_val = use_auth
        self._token_valid = token_valid
        self._reset_token_mock = Mock()
        self._aupdate_token_mock = AsyncMock()

    @property
    def _use_auth(self) -> bool:
        return self._use_auth_val

    def _is_token_usable(self) -> bool:
        return self._token_valid

    def _reset_token(self) -> None:
        self._reset_token_mock()
        self._token_valid = False

    async def _aupdate_token(self) -> None:
        await self._aupdate_token_mock()
        self._token_valid = True


class CallTracker:
    def __init__(self) -> None:
        self.count = 0


def test_with_auth_no_auth() -> None:
    client = MockAuthClient(use_auth=False)
    func = Mock(return_value="result")

    decorated = _with_auth(func)
    result = decorated(client)

    assert result == "result"
    client._update_token_mock.assert_not_called()
    func.assert_called_once()


def test_with_auth_valid_token() -> None:
    client = MockAuthClient(use_auth=True, token_valid=True)
    func = Mock(return_value="result")

    decorated = _with_auth(func)
    result = decorated(client)

    assert result == "result"
    client._update_token_mock.assert_not_called()
    func.assert_called_once()


def test_with_auth_invalid_token() -> None:
    client = MockAuthClient(use_auth=True, token_valid=False)
    func = Mock(return_value="result")

    decorated = _with_auth(func)
    result = decorated(client)

    assert result == "result"
    client._update_token_mock.assert_called_once()
    func.assert_called_once()


def test_with_auth_error_retry() -> None:
    client = MockAuthClient(use_auth=True, token_valid=True)
    # First call raises AuthenticationError, second call returns "result"
    func = Mock(side_effect=[AuthenticationError(url="url", status_code=401, content=b"", headers=None), "result"])

    decorated = _with_auth(func)
    result = decorated(client)

    assert result == "result"
    client._reset_token_mock.assert_called_once()
    client._update_token_mock.assert_called_once()
    assert func.call_count == 2


def test_with_auth_stream_no_auth() -> None:
    client = MockAuthClient(use_auth=False)
    func = Mock(return_value=iter(["chunk"]))

    decorated = _with_auth_stream(func)
    result = list(decorated(client))

    assert result == ["chunk"]
    client._update_token_mock.assert_not_called()
    func.assert_called_once()


def test_with_auth_stream_error_retry() -> None:
    client = MockAuthClient(use_auth=True, token_valid=True)
    tracker = CallTracker()

    def func(self: Any) -> Iterator[str]:
        if tracker.count == 0:
            tracker.count += 1
            raise AuthenticationError(url="url", status_code=401, content=b"", headers=None)
        yield "chunk"

    decorated = _with_auth_stream(func)
    result = list(decorated(client))

    assert result == ["chunk"]
    client._reset_token_mock.assert_called_once()
    client._update_token_mock.assert_called_once()


async def test_awith_auth_no_auth() -> None:
    client = MockAsyncAuthClient(use_auth=False)
    func = AsyncMock(return_value="result")

    decorated = _awith_auth(func)
    result = await decorated(client)

    assert result == "result"
    client._aupdate_token_mock.assert_not_called()
    func.assert_called_once()


async def test_awith_auth_error_retry() -> None:
    client = MockAsyncAuthClient(use_auth=True, token_valid=True)
    # First call raises AuthenticationError, second call returns "result"
    func = AsyncMock(side_effect=[AuthenticationError(url="url", status_code=401, content=b"", headers=None), "result"])

    decorated = _awith_auth(func)
    result = await decorated(client)

    assert result == "result"
    client._reset_token_mock.assert_called_once()
    client._aupdate_token_mock.assert_called_once()
    assert func.call_count == 2


async def test_awith_auth_stream_error_retry() -> None:
    client = MockAsyncAuthClient(use_auth=True, token_valid=True)
    tracker = CallTracker()

    async def func(self: Any) -> AsyncIterator[str]:
        if tracker.count == 0:
            tracker.count += 1
            raise AuthenticationError(url="url", status_code=401, content=b"", headers=None)
        yield "chunk"

    decorated = _awith_auth_stream(func)
    result = [chunk async for chunk in decorated(client)]

    assert result == ["chunk"]
    client._reset_token_mock.assert_called_once()
    client._aupdate_token_mock.assert_called_once()
