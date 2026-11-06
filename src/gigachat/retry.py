"""Classify retryable failures and retain bounded compatibility decorators."""

import asyncio
import functools
import logging
import math
import random
import ssl
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import Any, TypeVar, cast

import httpx2

from gigachat.exceptions import ResponseError
from gigachat.settings import Settings

logger = logging.getLogger(__name__)
T = TypeVar("T")


def _get_retry_settings(instance: Any) -> Settings:
    """Resolve settings from any client type."""
    if hasattr(instance, "_settings"):
        return cast(Settings, instance._settings)
    if hasattr(instance, "_base_client"):
        return cast(Settings, instance._base_client._settings)
    raise ValueError("Cannot resolve settings from client")


def _calculate_backoff(attempt: int, factor: float, exception: Exception) -> float:
    """Preserve finite server waits or calculate capped exponential backoff."""
    if isinstance(exception, ResponseError):
        server_delay = float(exception.retry_after)
        if math.isfinite(server_delay) and server_delay > 0:
            return server_delay
    return min(float(factor * 2 ** min(attempt, 30)) + random.uniform(0, 0.5), 60.0)


def _certificate_failure(exception: BaseException) -> bool:
    seen: set[int] = set()
    pending = [exception]
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(current):
            return True
        pending.extend(error for error in (current.__cause__, current.__context__) if error is not None)
    return False


def _should_retry(exception: Exception, retry_codes: tuple[int, ...]) -> bool:
    """Retry explicit statuses and transient network failures before response delivery."""
    if isinstance(exception, ResponseError):
        return exception.status_code in retry_codes
    if _certificate_failure(exception):
        return False
    return isinstance(
        exception,
        (
            httpx2.ConnectError,
            httpx2.ReadError,
            httpx2.WriteError,
            httpx2.CloseError,
            httpx2.ConnectTimeout,
            httpx2.ReadTimeout,
            httpx2.WriteTimeout,
            httpx2.RemoteProtocolError,
        ),
    )


class _Budget:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.started: float | None = None
        self.error: Exception | None = None

    def delay(self, attempt: int, error: Exception) -> float | None:
        if self.started is None:
            self.started = time.monotonic()
        self.error = error
        if attempt >= self.settings.max_retries or not _should_retry(error, self.settings.retry_on_status_codes):
            return None
        delay = _calculate_backoff(attempt, self.settings.retry_backoff_factor, error)
        remaining = self.settings.max_retry_time - (time.monotonic() - self.started)
        return delay if math.isfinite(delay) and 0 <= delay < remaining else None

    def check(self) -> None:
        if (
            self.started is not None
            and self.error is not None
            and time.monotonic() - self.started >= self.settings.max_retry_time
        ):
            raise self.error


def _with_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Retain bounded retry behavior for private compatibility callers."""

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
        budget = _Budget(_get_retry_settings(self))
        attempt = 0
        while True:
            budget.check()
            try:
                return func(self, *args, **kwargs)
            except Exception as error:
                delay = budget.delay(attempt, error)
                if delay is None:
                    raise
                logger.debug("Retry %d after %.2fs (%s)", attempt + 1, delay, type(error).__name__)
                time.sleep(delay)
                attempt += 1

    return wrapper


def _awith_retry(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Retain bounded async retry behavior for private compatibility callers."""

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
        budget = _Budget(_get_retry_settings(self))
        attempt = 0
        while True:
            budget.check()
            try:
                return await func(self, *args, **kwargs)
            except Exception as error:
                delay = budget.delay(attempt, error)
                if delay is None:
                    raise
                logger.debug("Async retry %d after %.2fs (%s)", attempt + 1, delay, type(error).__name__)
                await asyncio.sleep(delay)
                attempt += 1

    return wrapper


def _with_retry_stream(func: Callable[..., Iterator[T]]) -> Callable[..., Iterator[T]]:
    """Retry stream setup only until the first item has been delivered."""

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Iterator[T]:
        budget = _Budget(_get_retry_settings(self))
        attempt = 0
        emitted = False
        while True:
            budget.check()
            try:
                iterator = func(self, *args, **kwargs)
                try:
                    for item in iterator:
                        emitted = True
                        yield item
                finally:
                    close = getattr(iterator, "close", None)
                    if close is not None:
                        close()
                return
            except Exception as error:
                delay = None if emitted else budget.delay(attempt, error)
                if delay is None:
                    raise
                time.sleep(delay)
                attempt += 1

    return wrapper


def _awith_retry_stream(func: Callable[..., AsyncIterator[T]]) -> Callable[..., AsyncIterator[T]]:
    """Retry async stream setup only until the first item has been delivered."""

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> AsyncIterator[T]:
        budget = _Budget(_get_retry_settings(self))
        attempt = 0
        emitted = False
        while True:
            budget.check()
            try:
                iterator = func(self, *args, **kwargs)
                try:
                    async for item in iterator:
                        emitted = True
                        yield item
                finally:
                    close = getattr(iterator, "aclose", None)
                    if close is not None:
                        await close()
                return
            except Exception as error:
                delay = None if emitted else budget.delay(attempt, error)
                if delay is None:
                    raise
                await asyncio.sleep(delay)
                attempt += 1

    return wrapper
