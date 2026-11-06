"""Expose HTTP metadata without changing the API response model hierarchy."""

from collections.abc import AsyncGenerator, Callable, Generator
from types import TracebackType
from typing import Generic, NoReturn, TypeVar

import httpx2 as httpx

from gigachat.exceptions import APIConnectionError, APITimeoutError

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
