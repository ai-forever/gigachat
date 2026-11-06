"""Download generic file content through the shared request executor."""

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast

from gigachat._core.execution import request_scope
from gigachat._core.request import RequestOptions
from gigachat._core.response import AsyncStreamingResponse, StreamingResponse
from gigachat.api import files

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
        return files.stream_file_content_sync(client._client, file_id=file_id, access_token=client.token)

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
        return await files.stream_file_content_async(client._aclient, file_id=file_id, access_token=client.token)

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
