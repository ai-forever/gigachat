import asyncio
import functools
import logging
import random
import time
from typing import Any, AsyncIterator, Awaitable, Callable, Iterator, Tuple, TypeVar, cast

import httpx

from gigachat.exceptions import RateLimitError, ResponseError, ServerError
from gigachat.settings import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _get_retry_settings(instance: Any) -> Settings:
    """Resolve settings from any client type."""
    if hasattr(instance, "_settings"):
        return cast(Settings, instance._settings)
    if hasattr(instance, "_base_client"):
        return cast(Settings, instance._base_client._settings)
    raise ValueError(f"Cannot resolve settings from {instance}")


def _calculate_backoff(attempt: int, factor: float, exception: Exception) -> float:
    """Calculate delay with exponential backoff and jitter."""
    if isinstance(exception, RateLimitError) and exception.retry_after > 0:
        return float(exception.retry_after)

    base_delay = float(factor * (2**attempt))
    jitter = float(random.uniform(0, 0.5))
    return float(min(base_delay + jitter, 60.0))  # Cap at 60s


def _should_retry(exception: Exception, retry_codes: Tuple[int, ...]) -> bool:
    """Check if the exception should trigger a retry."""
    if isinstance(exception, (RateLimitError, ServerError, httpx.TransportError)):
        return True
    return isinstance(exception, ResponseError) and exception.status_code in retry_codes


def _with_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Decorate sync methods with retry logic."""

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
        settings = _get_retry_settings(self)
        max_retries = settings.max_retries

        if max_retries <= 0:
            return func(self, *args, **kwargs)

        backoff_factor = settings.retry_backoff_factor
        retry_codes = settings.retry_on_status_codes

        for attempt in range(max_retries + 1):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:  # noqa: PERF203
                if not _should_retry(e, retry_codes) or attempt == max_retries:
                    raise

                delay = _calculate_backoff(attempt, backoff_factor, e)
                logger.debug("Retry attempt %d/%d after %.2fs due to %s", attempt + 1, max_retries, delay, repr(e))
                time.sleep(delay)

        logger.info("All %d retries exhausted for %s", max_retries, func.__name__)
        raise RuntimeError("Unreachable")  # pragma: no cover

    return wrapper


def _with_retry_stream(func: Callable[..., Iterator[T]]) -> Callable[..., Iterator[T]]:
    """Decorate sync streaming methods with retry logic."""

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Iterator[T]:
        settings = _get_retry_settings(self)
        max_retries = settings.max_retries

        if max_retries <= 0:
            yield from func(self, *args, **kwargs)
            return

        backoff_factor = settings.retry_backoff_factor
        retry_codes = settings.retry_on_status_codes

        for attempt in range(max_retries + 1):
            try:
                yield from func(self, *args, **kwargs)
                return
            except Exception as e:  # noqa: PERF203
                if not _should_retry(e, retry_codes) or attempt == max_retries:
                    raise

                delay = _calculate_backoff(attempt, backoff_factor, e)
                logger.debug(
                    "Retry stream attempt %d/%d after %.2fs due to %s", attempt + 1, max_retries, delay, repr(e)
                )
                time.sleep(delay)

        logger.info("All %d retries exhausted for %s", max_retries, func.__name__)

    return wrapper


def _awith_retry(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorate async methods with retry logic."""

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> T:
        settings = _get_retry_settings(self)
        max_retries = settings.max_retries

        if max_retries <= 0:
            return await func(self, *args, **kwargs)

        backoff_factor = settings.retry_backoff_factor
        retry_codes = settings.retry_on_status_codes

        for attempt in range(max_retries + 1):
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:  # noqa: PERF203
                if not _should_retry(e, retry_codes) or attempt == max_retries:
                    raise

                delay = _calculate_backoff(attempt, backoff_factor, e)
                logger.debug(
                    "Retry async attempt %d/%d after %.2fs due to %s", attempt + 1, max_retries, delay, repr(e)
                )
                await asyncio.sleep(delay)

        logger.info("All %d retries exhausted for %s", max_retries, func.__name__)
        raise RuntimeError("Unreachable")  # pragma: no cover

    return wrapper


def _awith_retry_stream(func: Callable[..., AsyncIterator[T]]) -> Callable[..., AsyncIterator[T]]:
    """Decorate async streaming methods with retry logic."""

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> AsyncIterator[T]:
        settings = _get_retry_settings(self)
        max_retries = settings.max_retries

        if max_retries <= 0:
            async for chunk in func(self, *args, **kwargs):
                yield chunk
            return

        backoff_factor = settings.retry_backoff_factor
        retry_codes = settings.retry_on_status_codes

        for attempt in range(max_retries + 1):
            try:
                async for chunk in func(self, *args, **kwargs):
                    yield chunk
                return
            except Exception as e:  # noqa: PERF203
                if not _should_retry(e, retry_codes) or attempt == max_retries:
                    raise

                delay = _calculate_backoff(attempt, backoff_factor, e)
                logger.debug(
                    "Retry async stream attempt %d/%d after %.2fs due to %s",
                    attempt + 1,
                    max_retries,
                    delay,
                    repr(e),
                )
                await asyncio.sleep(delay)

        logger.info("All %d retries exhausted for %s", max_retries, func.__name__)

    return wrapper
