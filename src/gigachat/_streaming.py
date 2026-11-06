"""Own streaming responses and decode bounded, non-reconnecting SSE events."""

import json
from collections.abc import AsyncIterator, Callable, Iterator
from types import TracebackType
from typing import Generic, TypeVar

import httpx2 as httpx
from pydantic import BaseModel, ValidationError

from gigachat.exceptions import APIResponseValidationError, StreamInterruptedError

T = TypeVar("T", bound=BaseModel)
DEFAULT_MAX_EVENT_SIZE = 1024 * 1024


class _SyncEOFStream(httpx.SyncByteStream):
    def __init__(self, response: httpx.Response, *, flush_eof: bool) -> None:
        self.response = response
        self.flush_eof = flush_eof

    def __iter__(self) -> Iterator[bytes]:
        yield from self.response.iter_bytes()
        # Preserve the legacy EOF flush, but never flush after a transport failure.
        if self.flush_eof:
            yield b"\n\n"


class _AsyncEOFStream(httpx.AsyncByteStream):
    def __init__(self, response: httpx.Response, *, flush_eof: bool) -> None:
        self.response = response
        self.flush_eof = flush_eof

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self.response.aiter_bytes():
            yield chunk
        if self.flush_eof:
            yield b"\n\n"


def _source(
    response: httpx.Response, max_event_size: int | None, *, asynchronous: bool, flush_eof: bool
) -> httpx.EventSource:
    # Bytes have already been decompressed by the original response. Do not copy
    # Content-Encoding/Length, or the adapter would decode the stream twice.
    adapter = httpx.Response(
        response.status_code,
        headers={"content-type": response.headers.get("content-type", "")},
        stream=(
            _AsyncEOFStream(response, flush_eof=flush_eof)
            if asynchronous
            else _SyncEOFStream(response, flush_eof=flush_eof)
        ),
        request=response.request,
    )
    return httpx.EventSource(adapter, max_event_size=max_event_size)


def _parse_event(event: httpx.ServerSentEvent, model_class: type[T], event_mode: bool, response: httpx.Response) -> T:
    payload = json.loads(event.data)
    if event_mode and event.event != "message" and isinstance(payload, dict):
        payload.setdefault("event", event.event)
    chunk = model_class.model_validate(payload)
    if hasattr(chunk, "x_headers"):
        chunk.x_headers = {name: response.headers.get(name) for name in ("x-request-id", "x-session-id", "x-client-id")}
    return chunk


class _StreamMetadata:
    def __init__(self, response: httpx.Response | None) -> None:
        self._response = response
        self._response_getter: Callable[[], httpx.Response | None] | None = None
        self._headers = httpx.Headers()
        self._closed = False
        self.completed = False
        self._yielded = False

    @property
    def response(self) -> httpx.Response | None:
        if self._response_getter is not None:
            return self._response_getter()
        return self._response

    @property
    def headers(self) -> httpx.Headers:
        return self.response.headers if self.response is not None else self._headers

    @property
    def request_id(self) -> str | None:
        return self.headers.get("x-request-id")

    @property
    def status_code(self) -> int | None:
        return self.response.status_code if self.response is not None else None

    @property
    def url(self) -> httpx.URL | None:
        return self.response.url if self.response is not None else None

    @property
    def is_closed(self) -> bool:
        return self._closed

    def _record(self, chunk: BaseModel) -> None:
        self._yielded = True
        if self.response is not None and self.response.extensions.get("gigachat.stream_completed"):
            self.completed = True
        if self.response is None:
            self._headers.update(
                {key: value for key, value in (getattr(chunk, "x_headers", None) or {}).items() if value}
            )


class Stream(_StreamMetadata, Iterator[T], Generic[T]):
    """Iterate an owned SSE response; use a context manager for early exits.

    The event limit defaults to 1 MiB. Set it to None to disable the limit.
    A clean EOF flushes the final event for compatibility with legacy servers.
    """

    def __init__(
        self,
        response: httpx.Response,
        model_class: type[T],
        *,
        event_mode: bool = False,
        terminal_event: str | None = None,
        max_event_size: int | None = DEFAULT_MAX_EVENT_SIZE,
    ) -> None:
        super().__init__(response)
        self._decodes_response = True
        self._iterator = self._events(response, model_class, event_mode, max_event_size, terminal_event)

    @classmethod
    def from_iterator(
        cls, iterator: Iterator[T], *, response_getter: Callable[[], httpx.Response | None] | None = None
    ) -> "Stream[T]":
        """Wrap a lazy request iterator and forward its close operation."""
        stream = cls.__new__(cls)
        _StreamMetadata.__init__(stream, None)
        stream._decodes_response = False
        stream._iterator = iterator
        stream._response_getter = response_getter
        return stream

    def _events(
        self,
        response: httpx.Response,
        model_class: type[T],
        event_mode: bool,
        max_event_size: int | None,
        terminal_event: str | None,
    ) -> Iterator[T]:
        for event in _source(response, max_event_size, asynchronous=False, flush_eof=terminal_event is None):
            if event.data.strip() == "[DONE]":
                if terminal_event is None:
                    return
                break
            if not event.data.strip():
                continue
            chunk = _parse_event(event, model_class, event_mode, response)
            if terminal_event is not None and getattr(chunk, "event", event.event) == terminal_event:
                self.completed = True
                response.extensions["gigachat.stream_completed"] = True
                yield chunk
                return
            yield chunk
        if terminal_event is not None:
            raise StreamInterruptedError(
                f"Stream ended before {terminal_event}", request_id=self.request_id, partial_output=self._yielded
            )

    def __iter__(self) -> "Stream[T]":
        return self

    def __next__(self) -> T:
        if self._closed:
            raise StopIteration
        try:
            chunk = next(self._iterator)
        except StopIteration:
            self.completed = True
            self.close()
            raise
        except (ValidationError, json.JSONDecodeError, httpx.SSEError) as exc:
            self.close()
            if not self._decodes_response:
                raise
            raise APIResponseValidationError("Invalid streaming response", request_id=self.request_id) from exc
        except httpx.TransportError as exc:
            self.close()
            raise StreamInterruptedError(request_id=self.request_id, partial_output=self._yielded) from exc
        except BaseException:
            self.close()
            raise
        self._record(chunk)
        if self.completed:
            self.close()
        return chunk

    def close(self) -> None:
        """Close the iterator and response without closing its shared client."""
        if self._closed:
            return
        self._closed = True
        try:
            close = getattr(self._iterator, "close", None)
            if close is not None:
                close()
        finally:
            if self.response is not None:
                self.response.close()

    def __enter__(self) -> "Stream[T]":
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.close()


class AsyncStream(_StreamMetadata, AsyncIterator[T], Generic[T]):
    """Iterate an owned asynchronous SSE response with explicit cleanup."""

    def __init__(
        self,
        response: httpx.Response,
        model_class: type[T],
        *,
        event_mode: bool = False,
        terminal_event: str | None = None,
        max_event_size: int | None = DEFAULT_MAX_EVENT_SIZE,
    ) -> None:
        super().__init__(response)
        self._decodes_response = True
        self._iterator = self._events(response, model_class, event_mode, max_event_size, terminal_event)

    @classmethod
    def from_iterator(
        cls, iterator: AsyncIterator[T], *, response_getter: Callable[[], httpx.Response | None] | None = None
    ) -> "AsyncStream[T]":
        """Wrap a lazy request iterator and forward its aclose operation."""
        stream = cls.__new__(cls)
        _StreamMetadata.__init__(stream, None)
        stream._decodes_response = False
        stream._iterator = iterator
        stream._response_getter = response_getter
        return stream

    async def _events(
        self,
        response: httpx.Response,
        model_class: type[T],
        event_mode: bool,
        max_event_size: int | None,
        terminal_event: str | None,
    ) -> AsyncIterator[T]:
        async for event in _source(response, max_event_size, asynchronous=True, flush_eof=terminal_event is None):
            if event.data.strip() == "[DONE]":
                if terminal_event is None:
                    return
                break
            if not event.data.strip():
                continue
            chunk = _parse_event(event, model_class, event_mode, response)
            if terminal_event is not None and getattr(chunk, "event", event.event) == terminal_event:
                self.completed = True
                response.extensions["gigachat.stream_completed"] = True
                yield chunk
                return
            yield chunk
        if terminal_event is not None:
            raise StreamInterruptedError(
                f"Stream ended before {terminal_event}", request_id=self.request_id, partial_output=self._yielded
            )

    def __aiter__(self) -> "AsyncStream[T]":
        return self

    async def __anext__(self) -> T:
        if self._closed:
            raise StopAsyncIteration
        try:
            chunk = await self._iterator.__anext__()
        except StopAsyncIteration:
            self.completed = True
            await self.aclose()
            raise
        except (ValidationError, json.JSONDecodeError, httpx.SSEError) as exc:
            await self.aclose()
            if not self._decodes_response:
                raise
            raise APIResponseValidationError("Invalid streaming response", request_id=self.request_id) from exc
        except httpx.TransportError as exc:
            await self.aclose()
            raise StreamInterruptedError(request_id=self.request_id, partial_output=self._yielded) from exc
        except BaseException:
            await self.aclose()
            raise
        self._record(chunk)
        if self.completed:
            await self.aclose()
        return chunk

    async def aclose(self) -> None:
        """Close the iterator and response without closing its shared client."""
        if self._closed:
            return
        self._closed = True
        try:
            close = getattr(self._iterator, "aclose", None)
            if close is not None:
                await close()
        finally:
            if self.response is not None:
                await self.response.aclose()

    async def __aenter__(self) -> "AsyncStream[T]":
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> None:
        await self.aclose()
