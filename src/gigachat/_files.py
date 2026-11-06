"""Download generic file content through the shared request executor."""

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast
from urllib.parse import quote

from gigachat._execution import request_scope, send_async, send_sync
from gigachat._request_options import RequestOptions
from gigachat._response import AsyncStreamingResponse, StreamingResponse
from gigachat.api.utils import _raise_for_status, build_headers

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class SyncFilesMixin:
    """Expose binary file reads and bounded-memory downloads."""

    @request_scope
    def stream_file_content(
        self, file_id: str, *, request_options: RequestOptions | None = None
    ) -> StreamingResponse[bytes]:
        """Open a file byte stream; use with to guarantee response cleanup."""
        client = cast("GigaChatSyncClient", self)
        response = send_sync(
            client._client,
            stream=True,
            method="GET",
            url=f"/files/{quote(file_id, safe='')}/content",
            headers={**build_headers(client.token), "Accept": "application/octet-stream"},
        )
        if response.status_code != 200:
            try:
                _raise_for_status(response.url, response.status_code, response.read(), response.headers)
            finally:
                response.close()
        return StreamingResponse(response, lambda result: result.content)

    def get_file_content(self, file_id: str, *, request_options: RequestOptions | None = None) -> bytes:
        """Read a complete binary file into memory without base64 conversion."""
        with self.stream_file_content(file_id, request_options=request_options) as response:
            return response.read()

    def download_file(
        self, file_id: str, destination: str | Path, *, request_options: RequestOptions | None = None
    ) -> Path:
        """Stream a file to disk and replace the destination only after success."""
        target = Path(destination)
        temporary: Path | None = None
        try:
            with self.stream_file_content(file_id, request_options=request_options) as response:
                with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", delete=False) as output:
                    temporary = Path(output.name)
                    for chunk in response.iter_bytes(64 * 1024):
                        output.write(chunk)
            os.replace(temporary, target)
            return target
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


class AsyncFilesMixin:
    """Expose async binary file reads and bounded-memory downloads."""

    @request_scope
    async def astream_file_content(
        self, file_id: str, *, request_options: RequestOptions | None = None
    ) -> AsyncStreamingResponse[bytes]:
        """Open an async file byte stream; use async with after awaiting it."""
        client = cast("GigaChatAsyncClient", self)
        response = await send_async(
            client._aclient,
            stream=True,
            method="GET",
            url=f"/files/{quote(file_id, safe='')}/content",
            headers={**build_headers(client.token), "Accept": "application/octet-stream"},
        )
        if response.status_code != 200:
            try:
                _raise_for_status(response.url, response.status_code, await response.aread(), response.headers)
            finally:
                await response.aclose()
        return AsyncStreamingResponse(response, lambda result: result.content)

    async def aget_file_content(self, file_id: str, *, request_options: RequestOptions | None = None) -> bytes:
        """Read a complete binary file into memory without base64 conversion."""
        async with await self.astream_file_content(file_id, request_options=request_options) as response:
            return await response.read()

    async def adownload_file(
        self, file_id: str, destination: str | Path, *, request_options: RequestOptions | None = None
    ) -> Path:
        """Stream a file to disk and replace the destination only after success."""
        target = Path(destination)
        temporary: Path | None = None
        try:
            async with await self.astream_file_content(file_id, request_options=request_options) as response:
                with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", delete=False) as output:
                    temporary = Path(output.name)
                    async for chunk in response.iter_bytes(64 * 1024):
                        output.write(chunk)
            os.replace(temporary, target)
            return target
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
