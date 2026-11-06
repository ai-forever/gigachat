"""HTTPX2 transport based on the BSD-licensed httpx-aiohttp adapter."""

import asyncio
import contextlib
import ssl
from collections.abc import AsyncIterator, Iterator
from typing import Any

import aiohttp
import httpx2


@contextlib.contextmanager
def map_aiohttp_exceptions() -> Iterator[None]:
    """Translate only aiohttp transport failures to HTTPX2 errors."""
    try:
        yield
    except aiohttp.ConnectionTimeoutError as exc:
        raise httpx2.ConnectTimeout(str(exc)) from exc
    except (aiohttp.SocketTimeoutError, asyncio.TimeoutError) as exc:
        raise httpx2.ReadTimeout(str(exc)) from exc
    except (aiohttp.ClientProxyConnectionError, aiohttp.ClientHttpProxyError) as exc:
        raise httpx2.ProxyError(str(exc)) from exc
    except aiohttp.ClientConnectorError as exc:
        raise httpx2.ConnectError(str(exc)) from exc
    except (aiohttp.ClientConnectionError, aiohttp.ClientPayloadError) as exc:
        raise httpx2.ReadError(str(exc)) from exc
    except aiohttp.InvalidURL as exc:
        raise httpx2.UnsupportedProtocol(str(exc)) from exc


def validate_borrowed_session(session: aiohttp.ClientSession) -> None:
    """Reject hidden session credentials while preserving caller ownership."""
    if session.auth is not None or "Authorization" in session.headers:
        raise ValueError(
            "Borrowed aiohttp sessions cannot define default auth or an Authorization header; "
            "configure HTTPX2 client headers instead"
        )


class AiohttpResponseStream(httpx2.AsyncByteStream):
    def __init__(self, response: aiohttp.ClientResponse) -> None:
        self.response = response

    async def __aiter__(self) -> AsyncIterator[bytes]:
        with map_aiohttp_exceptions():
            async for chunk in self.response.content.iter_chunked(16384):
                yield chunk

    async def aclose(self) -> None:
        self.response.close()


class AiohttpTransport(httpx2.AsyncBaseTransport):
    def __init__(
        self,
        *,
        verify: ssl.SSLContext,
        limits: httpx2.Limits,
        proxy: httpx2.Proxy | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.verify = verify
        self.limits = limits
        self.proxy = proxy
        self.session = session
        self.owns_session = session is None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        loop = asyncio.get_running_loop()
        if self._loop is not None and self._loop is not loop:
            raise RuntimeError("aiohttp transport cannot be used from a different event loop")
        self._loop = loop
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=self.limits.max_connections or 0, keepalive_timeout=self.limits.keepalive_expiry, ssl=self.verify
            )
            self.session = aiohttp.ClientSession(connector=connector, auto_decompress=False, trust_env=False)
        if not self.owns_session:
            validate_borrowed_session(self.session)
        timeout = request.extensions.get("timeout", {})
        connect, pool, write = timeout.get("connect"), timeout.get("pool"), timeout.get("write")
        if write is not None:
            raise ValueError("aiohttp transport does not support a separate write timeout")
        if pool is not None and connect is not None and pool != connect:
            raise ValueError("aiohttp transport requires equal connect and pool timeouts when both are set")
        try:
            data: Any = request.content or None
        except httpx2.RequestNotRead:
            data = request.stream
        headers = list(request.headers.multi_items())
        if data is not None and not isinstance(data, bytes):
            headers = [(k, v) for k, v in headers if k.lower() != "transfer-encoding"]
        with map_aiohttp_exceptions():
            response = await self.session.request(
                request.method,
                str(request.url),
                headers=headers,
                data=data,
                allow_redirects=False,
                auto_decompress=False,
                ssl=self.verify,
                timeout=aiohttp.ClientTimeout(
                    total=None, connect=pool, sock_connect=connect, sock_read=timeout.get("read")
                ),
                server_hostname=request.extensions.get("sni_hostname"),
                proxy=str(self.proxy.url) if self.proxy else None,
                proxy_auth=aiohttp.BasicAuth(*self.proxy.auth) if self.proxy and self.proxy.auth else None,
                proxy_headers=self.proxy.headers if self.proxy else None,
            )
        return httpx2.Response(
            response.status,
            headers=response.raw_headers,
            request=request,
            stream=AiohttpResponseStream(response),
            extensions={"http_version": b"HTTP/1.1", "reason_phrase": (response.reason or "").encode()},
        )

    async def aclose(self) -> None:
        if self.owns_session and self.session is not None:
            await self.session.close()
