import functools
import logging
from typing import Any, AsyncIterator, Awaitable, Callable, Iterator, Protocol, TypeVar, runtime_checkable

from gigachat.exceptions import AuthenticationError

__all__ = [
    "AuthClientProtocol",
    "AsyncAuthClientProtocol",
    "with_auth",
    "with_auth_stream",
    "awith_auth",
    "awith_auth_stream",
]

_logger = logging.getLogger(__name__)

T = TypeVar("T")


@runtime_checkable
class AuthClientProtocol(Protocol):
    """Protocol for synchronous authentication client."""

    @property
    def _use_auth(self) -> bool:
        ...

    def _check_validity_token(self) -> bool:
        ...

    def _reset_token(self) -> None:
        ...

    def _update_token(self) -> None:
        ...


@runtime_checkable
class AsyncAuthClientProtocol(Protocol):
    """Protocol for asynchronous authentication client."""

    @property
    def _use_auth(self) -> bool:
        ...

    def _check_validity_token(self) -> bool:
        ...

    def _reset_token(self) -> None:
        ...

    async def _aupdate_token(self) -> None:
        ...


def _get_auth_client(instance: Any) -> AuthClientProtocol:
    """Resolve the synchronous auth client from the instance."""
    if isinstance(instance, AuthClientProtocol):
        return instance
    if hasattr(instance, "_client") and isinstance(instance._client, AuthClientProtocol):
        return instance._client
    if hasattr(instance, "base_client") and isinstance(instance.base_client, AuthClientProtocol):
        return instance.base_client
    raise ValueError(f"Could not resolve AuthClientProtocol from {instance}")


def _get_async_auth_client(instance: Any) -> AsyncAuthClientProtocol:
    """Resolve the asynchronous auth client from the instance."""
    if isinstance(instance, AsyncAuthClientProtocol):
        return instance
    if hasattr(instance, "_client") and isinstance(instance._client, AsyncAuthClientProtocol):
        return instance._client
    if hasattr(instance, "base_client") and isinstance(instance.base_client, AsyncAuthClientProtocol):
        return instance.base_client
    raise ValueError(f"Could not resolve AsyncAuthClientProtocol from {instance}")


def with_auth(func: Callable[..., T]) -> Callable[..., T]:
    """Decorate synchronous authenticated requests."""

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
        auth_client = _get_auth_client(self)
        if auth_client._use_auth:
            if auth_client._check_validity_token():
                try:
                    return func(self, *args, **kwargs)
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    auth_client._reset_token()
            auth_client._update_token()
        return func(self, *args, **kwargs)

    return wrapper


def with_auth_stream(func: Callable[..., Iterator[T]]) -> Callable[..., Iterator[T]]:
    """Decorate synchronous streaming requests."""

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Iterator[T]:
        auth_client = _get_auth_client(self)
        if auth_client._use_auth:
            if auth_client._check_validity_token():
                try:
                    yield from func(self, *args, **kwargs)
                    return
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    auth_client._reset_token()
            auth_client._update_token()
        yield from func(self, *args, **kwargs)

    return wrapper


def awith_auth(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorate asynchronous authenticated requests."""

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
        auth_client = _get_async_auth_client(self)
        if auth_client._use_auth:
            if auth_client._check_validity_token():
                try:
                    return await func(self, *args, **kwargs)
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    auth_client._reset_token()
            await auth_client._aupdate_token()
        return await func(self, *args, **kwargs)

    return wrapper


def awith_auth_stream(func: Callable[..., AsyncIterator[T]]) -> Callable[..., AsyncIterator[T]]:
    """Decorate asynchronous streaming requests."""

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> AsyncIterator[T]:
        auth_client = _get_async_auth_client(self)
        if auth_client._use_auth:
            if auth_client._check_validity_token():
                try:
                    async for chunk in func(self, *args, **kwargs):
                        yield chunk
                    return
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    auth_client._reset_token()
            await auth_client._aupdate_token()
        async for chunk in func(self, *args, **kwargs):
            yield chunk

    return wrapper
