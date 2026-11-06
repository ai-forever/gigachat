"""Expose HTTP metadata without changing the API response model hierarchy."""

import json
import logging
from collections.abc import AsyncGenerator, Callable, Generator
from http import HTTPStatus
from types import TracebackType
from typing import Generic, NoReturn, TypeVar

import httpx2 as httpx
from pydantic import BaseModel, ValidationError

from gigachat.exceptions import (
    APIConnectionError,
    APIResponseValidationError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RequestEntityTooLargeError,
    ResponseError,
    ServerError,
    UnprocessableEntityError,
)
from gigachat.models.base import APIResponse

T = TypeVar("T")


class _ResponseMetadata:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response

    @property
    def headers(self) -> httpx.Headers:
        return self.response.headers

    @property
    def status_code(self) -> int:
        return self.response.status_code

    @property
    def request_id(self) -> str | None:
        return self.headers.get("x-request-id")

    @property
    def url(self) -> httpx.URL:
        return self.response.url

    @property
    def is_closed(self) -> bool:
        return self.response.is_closed

    def _raise_read_error(self, error: httpx.TransportError) -> NoReturn:
        if isinstance(error, httpx.TimeoutException):
            raise APITimeoutError("Response read timed out", request_id=self.request_id) from error
        raise APIConnectionError("Response read failed", request_id=self.request_id) from error


class RawResponse(_ResponseMetadata, Generic[T]):
    """Parse an already fully read response synchronously, including after async requests."""

    def __init__(self, response: httpx.Response, parser: Callable[[httpx.Response], T]) -> None:
        super().__init__(response)
        # Fail immediately if the caller accidentally passed an unread stream.
        self.content = response.content
        self._parser = parser

    @property
    def text(self) -> str:
        return self.response.text

    def parse(self) -> T:
        """Convert the buffered response into its typed value without network I/O."""
        return self._parser(self.response)


class StreamingResponse(_ResponseMetadata, Generic[T]):
    """Own a sync byte response; close explicitly or use a context manager."""

    def __init__(self, response: httpx.Response, parser: Callable[[httpx.Response], T]) -> None:
        super().__init__(response)
        self._parser = parser

    def read(self) -> bytes:
        try:
            return self.response.read()
        except httpx.TransportError as error:
            self._raise_read_error(error)
        finally:
            self.close()

    def parse(self) -> T:
        self.read()
        return self._parser(self.response)

    def iter_bytes(self, chunk_size: int | None = None) -> Generator[bytes, None, None]:
        try:
            yield from self.response.iter_bytes(chunk_size)
        except httpx.TransportError as error:
            self._raise_read_error(error)
        finally:
            self.close()

    def close(self) -> None:
        self.response.close()

    def __enter__(self) -> "StreamingResponse[T]":
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.close()


class AsyncStreamingResponse(_ResponseMetadata, Generic[T]):
    """Own an async byte response with awaited reads, parsing and cleanup."""

    def __init__(self, response: httpx.Response, parser: Callable[[httpx.Response], T]) -> None:
        super().__init__(response)
        self._parser = parser

    async def read(self) -> bytes:
        try:
            return await self.response.aread()
        except httpx.TransportError as error:
            self._raise_read_error(error)
        finally:
            await self.aclose()

    async def parse(self) -> T:
        await self.read()
        return self._parser(self.response)

    async def iter_bytes(self, chunk_size: int | None = None) -> AsyncGenerator[bytes, None]:
        try:
            async for chunk in self.response.aiter_bytes(chunk_size):
                yield chunk
        except httpx.TransportError as error:
            self._raise_read_error(error)
        finally:
            await self.aclose()

    async def aclose(self) -> None:
        await self.response.aclose()

    async def __aenter__(self) -> "AsyncStreamingResponse[T]":
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> None:
        await self.aclose()


logger = logging.getLogger(__name__)
EVENT_STREAM = "text/event-stream"
ModelT = TypeVar("ModelT", bound=BaseModel)


def parse_data_chunk(line: str, model_class: type[ModelT]) -> ModelT | None:
    """Parse an SSE data line."""
    name, _, value = line.partition(":")
    if name == "data":
        value = value.lstrip()
        if value == "[DONE]":
            return None
        return model_class.model_validate_json(value)
    return None


def parse_chunk(line: str, model_class: type[ModelT]) -> ModelT | None:
    """Parse an SSE data line."""
    return parse_data_chunk(line, model_class)


def parse_event_chunk(event: str | None, data: str, model_class: type[ModelT]) -> ModelT:
    """Parse an SSE event with an optional event name."""
    payload = json.loads(data)
    if event and isinstance(payload, dict):
        payload.setdefault("event", event)
    return model_class.model_validate(payload)


def build_x_headers(response: httpx.Response) -> dict[str, str | None]:
    """Extract X-Headers from response."""
    return {
        "x-request-id": response.headers.get("x-request-id"),
        "x-session-id": response.headers.get("x-session-id"),
        "x-client-id": response.headers.get("x-client-id"),
    }


def _check_content_type(response: httpx.Response) -> None:
    content_type, _, _ = response.headers.get("content-type", "").partition(";")
    if content_type.strip().lower() != EVENT_STREAM:
        raise APIResponseValidationError(
            f"Expected response Content-Type to be '{EVENT_STREAM}', got {content_type!r}",
            request_id=response.headers.get("x-request-id"),
        )


def _raise_for_status(url: httpx.URL | str, status_code: int, content: bytes, headers: httpx.Headers) -> NoReturn:
    if status_code == HTTPStatus.BAD_REQUEST:
        raise BadRequestError(url, status_code, content, headers)
    elif status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(url, status_code, content, headers)
    elif status_code == HTTPStatus.FORBIDDEN:
        raise ForbiddenError(url, status_code, content, headers)
    elif status_code == HTTPStatus.NOT_FOUND:
        raise NotFoundError(url, status_code, content, headers)
    elif status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE:
        raise RequestEntityTooLargeError(url, status_code, content, headers)
    elif status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        raise UnprocessableEntityError(url, status_code, content, headers)
    elif status_code == HTTPStatus.TOO_MANY_REQUESTS:
        if retry_after := headers.get("retry-after"):
            logger.warning("Rate limit exceeded (429). Retry-After: %s", retry_after)
        else:
            logger.warning("Rate limit exceeded (429)")
        raise RateLimitError(url, status_code, content, headers)
    elif 500 <= status_code < 600:
        logger.warning("Server error (%d)", status_code)
        raise ServerError(url, status_code, content, headers)
    else:
        raise ResponseError(url, status_code, content, headers)


def _check_response(response: httpx.Response) -> None:
    if response.status_code == HTTPStatus.OK:
        _check_content_type(response)
    else:
        _raise_for_status(response.url, response.status_code, response.read(), response.headers)


async def _acheck_response(response: httpx.Response) -> None:
    if response.status_code == HTTPStatus.OK:
        _check_content_type(response)
    else:
        _raise_for_status(response.url, response.status_code, await response.aread(), response.headers)


def build_response(response: httpx.Response, model_class: type[ModelT]) -> ModelT:
    """Parse successful response into Pydantic model or raise error."""
    if response.status_code != HTTPStatus.OK:
        _raise_for_status(response.url, response.status_code, response.content, response.headers)
    try:
        payload = response.json()
        if isinstance(payload, dict):
            payload = {**payload, "x_headers": build_x_headers(response)}
        result = model_class.model_validate(payload)
        if isinstance(result, APIResponse):
            result.x_headers = build_x_headers(response)
        return result
    except (ValidationError, json.JSONDecodeError) as exc:
        raise APIResponseValidationError(
            "Invalid API response", request_id=response.headers.get("x-request-id")
        ) from exc
