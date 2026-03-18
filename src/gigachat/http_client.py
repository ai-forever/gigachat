from __future__ import annotations

import ssl
from typing import Any, AsyncContextManager, AsyncIterator, Dict, Optional, Protocol, Union, cast

import httpx

from gigachat.settings import Settings

aiohttp: Any

try:
    import aiohttp
except ImportError:  # pragma: no cover - exercised in environments without aiohttp installed
    aiohttp = None


class AsyncStreamResponse(Protocol):
    status_code: int
    headers: httpx.Headers
    url: Union[httpx.URL, str]

    async def aread(self) -> bytes: ...

    def aiter_lines(self) -> AsyncIterator[str]: ...


class AsyncHttpClient(Protocol):
    async def request(self, **kwargs: Any) -> httpx.Response: ...

    def stream(self, **kwargs: Any) -> AsyncContextManager[AsyncStreamResponse]: ...

    async def aclose(self) -> None: ...


class AsyncHttpClientFactory(Protocol):
    def create_client(self, settings: Settings) -> AsyncHttpClient: ...

    def create_auth_client(self, settings: Settings) -> AsyncHttpClient: ...


def _get_kwargs(settings: Settings) -> Dict[str, Any]:
    """Return settings for connecting to the GigaChat API."""
    kwargs = {
        "base_url": settings.base_url,
        "verify": settings.verify_ssl_certs,
        "timeout": httpx.Timeout(settings.timeout),
    }
    if settings.ssl_context:
        kwargs["verify"] = settings.ssl_context
    if settings.ca_bundle_file:
        kwargs["verify"] = settings.ca_bundle_file
    if settings.cert_file:
        kwargs["cert"] = (
            settings.cert_file,
            settings.key_file,
            settings.key_file_password,
        )
    if settings.max_connections is not None:
        kwargs["limits"] = httpx.Limits(max_connections=settings.max_connections)
    return kwargs


def _get_auth_kwargs(settings: Settings) -> Dict[str, Any]:
    """Return settings for connecting to the OAuth 2.0 authorization server."""
    kwargs = {
        "verify": settings.verify_ssl_certs,
        "timeout": httpx.Timeout(settings.timeout),
    }
    if settings.ssl_context:
        kwargs["verify"] = settings.ssl_context
    if settings.ca_bundle_file:
        kwargs["verify"] = settings.ca_bundle_file
    return kwargs


def _require_aiohttp() -> Any:
    if aiohttp is None:
        raise ImportError(
            "aiohttp is required to use DefaultAioHttpClient. Install it with `pip install gigachat[aiohttp]`."
        )
    return aiohttp


def _build_ssl_context(settings: Settings, *, use_client_cert: bool) -> Optional[Union[bool, ssl.SSLContext]]:
    if settings.ssl_context:
        return settings.ssl_context

    if not settings.verify_ssl_certs:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    elif settings.ca_bundle_file:
        context = ssl.create_default_context(cafile=settings.ca_bundle_file)
    elif settings.cert_file and use_client_cert:
        context = ssl.create_default_context()
    else:
        return None

    if settings.cert_file and use_client_cert:
        context.load_cert_chain(settings.cert_file, settings.key_file, settings.key_file_password)

    return context


def _build_request_builder(base_url: Optional[str] = None) -> httpx.AsyncClient:
    kwargs: Dict[str, Any] = {}
    if base_url is not None:
        kwargs["base_url"] = base_url
    return httpx.AsyncClient(**kwargs)


class _AioHttpStreamResponse:
    _response: Any
    status_code: int
    headers: httpx.Headers
    url: Union[httpx.URL, str]

    def __init__(self, response: Any):
        self._response = response
        self.status_code = response.status
        self.headers = httpx.Headers(response.headers)
        self.url = httpx.URL(str(response.url))

    async def aread(self) -> bytes:
        return cast(bytes, await self._response.read())

    async def aiter_lines(self) -> AsyncIterator[str]:
        encoding = self._response.charset or "utf-8"
        while True:
            line = await self._response.content.readline()
            if not line:
                break
            yield line.decode(encoding, errors="replace").rstrip("\r\n")


class _AioHttpStreamContext:
    def __init__(self, client: _AioHttpClient, kwargs: Dict[str, Any]):
        self._client = client
        self._kwargs = kwargs
        self._request_context: Optional[Any] = None

    async def __aenter__(self) -> _AioHttpStreamResponse:
        request, request_kwargs = await self._client.build_aiohttp_request(self._kwargs)
        try:
            self._request_context = self._client._session.request(request.method, str(request.url), **request_kwargs)
            response = await self._request_context.__aenter__()
        except Exception as exc:
            raise self._client.map_transport_error(exc) from exc
        return _AioHttpStreamResponse(response)

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._request_context is not None:
            await self._request_context.__aexit__(exc_type, exc, tb)


class _AioHttpClient:
    def __init__(self, *, settings: Settings, base_url: Optional[str], use_client_cert: bool):
        aiohttp_module = _require_aiohttp()
        connector_kwargs: Dict[str, Any] = {}
        ssl_context = _build_ssl_context(settings, use_client_cert=use_client_cert)
        if ssl_context is not None:
            connector_kwargs["ssl"] = ssl_context
        if settings.max_connections is not None:
            connector_kwargs["limit"] = settings.max_connections

        self._session = aiohttp_module.ClientSession(
            timeout=aiohttp_module.ClientTimeout(total=settings.timeout),
            connector=aiohttp_module.TCPConnector(**connector_kwargs),
        )
        self._request_builder = _build_request_builder(base_url)

    def map_transport_error(self, exc: Exception) -> Exception:
        aiohttp_module = _require_aiohttp()
        if isinstance(exc, aiohttp_module.ClientError):
            return httpx.TransportError(str(exc))
        if isinstance(exc, TimeoutError):
            return httpx.TransportError("Request timed out")
        return exc

    async def build_aiohttp_request(self, kwargs: Dict[str, Any]) -> tuple[httpx.Request, Dict[str, Any]]:
        request = self._request_builder.build_request(**kwargs)
        content = await request.aread()
        request_kwargs: Dict[str, Any] = {"headers": dict(request.headers)}
        if content:
            request_kwargs["data"] = content
        return request, request_kwargs

    async def request(self, **kwargs: Any) -> httpx.Response:
        request, request_kwargs = await self.build_aiohttp_request(kwargs)
        try:
            async with self._session.request(request.method, str(request.url), **request_kwargs) as response:
                content = await response.read()
        except Exception as exc:
            raise self.map_transport_error(exc) from exc

        return httpx.Response(
            status_code=response.status,
            headers=httpx.Headers(response.headers),
            content=content,
            request=request,
        )

    def stream(self, **kwargs: Any) -> AsyncContextManager[AsyncStreamResponse]:
        return cast(AsyncContextManager[AsyncStreamResponse], _AioHttpStreamContext(self, kwargs))

    async def aclose(self) -> None:
        await self._session.close()
        await self._request_builder.aclose()


class DefaultAioHttpClient:
    """Create aiohttp-backed async HTTP clients for GigaChat async clients."""

    def create_client(self, settings: Settings) -> AsyncHttpClient:
        return _AioHttpClient(settings=settings, base_url=settings.base_url, use_client_cert=True)

    def create_auth_client(self, settings: Settings) -> AsyncHttpClient:
        return _AioHttpClient(settings=settings, base_url=None, use_client_cert=False)


__all__ = ["DefaultAioHttpClient"]
