"""HTTPX2 client defaults and the optional aiohttp transport."""

import ssl
from typing import Any

import httpx2

from gigachat._core.request import _aiohttp_timeout


def http_client_kwargs(settings: Any, *, for_auth: bool = False, backend: str | None = None) -> dict[str, Any]:
    """Translate SDK settings into common native HTTPX2 client options."""
    trust_env = getattr(settings, "trust_env", True)
    verify = build_ssl_context(
        verify_ssl_certs=settings.verify_ssl_certs,
        ssl_context=settings.ssl_context,
        auth_ssl_context=getattr(settings, "auth_ssl_context", None),
        ca_bundle_file=settings.ca_bundle_file,
        cert_file=settings.cert_file,
        key_file=settings.key_file,
        key_file_password=settings.key_file_password,
        trust_env=trust_env,
        for_auth=for_auth,
    )
    result: dict[str, Any] = {"verify": verify, "timeout": settings.timeout, "trust_env": trust_env}
    if getattr(settings, "proxy", None) is not None:
        result["proxy"] = settings.proxy
    backend = backend or getattr(settings, "async_backend", "httpx2")
    limits = getattr(settings, "limits", None)
    if limits is not None and settings.max_connections is not None:
        raise ValueError("limits and max_connections cannot both be set")
    if limits is not None:
        result["limits"] = limits
    elif settings.max_connections is not None:
        if settings.max_connections <= 0:
            raise ValueError("max_connections must be positive")
        if backend == "aiohttp":
            result["limits"] = httpx2.Limits(max_connections=settings.max_connections, max_keepalive_connections=None)
        else:
            result["limits"] = httpx2.Limits(max_connections=settings.max_connections)
    if getattr(settings, "http2", False):
        result["http2"] = True
    return result


class DefaultHttpxClient(httpx2.Client):
    """Synchronous HTTPX2 client with GigaChat defaults."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("timeout", 30.0)
        super().__init__(**kwargs)


class DefaultAsyncHttpxClient(httpx2.AsyncClient):
    """Asynchronous HTTPX2 client with GigaChat defaults."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("timeout", 30.0)
        super().__init__(**kwargs)


class DefaultAioHttpClient(httpx2.AsyncClient):
    """HTTPX2-compatible async client owning its lazy aiohttp sessions."""

    def __init__(self, **kwargs: Any) -> None:
        try:
            __import__("aiohttp")
        except ImportError as exc:
            raise ImportError('Install the aiohttp extra with pip install "gigachat[aiohttp]"') from exc
        if kwargs.get("http2", False) or not kwargs.get("http1", True):
            raise ValueError("aiohttp transport supports HTTP/1.1 only")
        if kwargs.get("cert") is not None:
            raise ValueError("Pass client certificates through an SSLContext via verify")
        if kwargs.get("transport") is not None or kwargs.get("mounts") is not None:
            raise ValueError("aiohttp client does not support custom transport or mounts")
        limits = kwargs.setdefault("limits", httpx2.Limits(max_connections=100, max_keepalive_connections=None))
        if limits.max_keepalive_connections is not None:
            raise ValueError("aiohttp transport does not support max_keepalive_connections")
        if limits.max_connections is not None and limits.max_connections <= 0:
            raise ValueError("max_connections must be positive or None for unlimited")
        if limits.keepalive_expiry is not None and limits.keepalive_expiry < 0:
            raise ValueError("keepalive_expiry must be non-negative")
        kwargs["timeout"] = _aiohttp_timeout(kwargs.get("timeout", 30.0))
        super().__init__(**kwargs)

    def build_request(self, *args: Any, **kwargs: Any) -> httpx2.Request:
        if "timeout" in kwargs and not isinstance(kwargs["timeout"], httpx2._client.UseClientDefault):
            kwargs["timeout"] = _aiohttp_timeout(kwargs["timeout"])
        return super().build_request(*args, **kwargs)

    def _init_transport(
        self,
        verify: ssl.SSLContext | str | bool = True,
        cert: Any = None,
        trust_env: bool = True,
        http1: bool = True,
        http2: bool = False,
        limits: httpx2.Limits | None = None,
        transport: httpx2.AsyncBaseTransport | None = None,
        **kwargs: Any,
    ) -> httpx2.AsyncBaseTransport:
        from gigachat._vendor.httpx_aiohttp.transport import AiohttpTransport

        if limits is None:
            raise ValueError("limits must be configured")
        context = httpx2.create_ssl_context(verify=verify, trust_env=trust_env)
        return AiohttpTransport(verify=context, limits=limits)

    def _init_proxy_transport(
        self,
        proxy: httpx2.Proxy,
        verify: ssl.SSLContext | str | bool = True,
        cert: Any = None,
        trust_env: bool = True,
        http1: bool = True,
        http2: bool = False,
        limits: httpx2.Limits | None = None,
        **kwargs: Any,
    ) -> httpx2.AsyncBaseTransport:
        from gigachat._vendor.httpx_aiohttp.transport import AiohttpTransport

        if limits is None:
            raise ValueError("limits must be configured")
        if proxy.url.scheme not in ("http", "https"):
            raise ValueError("aiohttp transport supports only HTTP and HTTPS proxies")
        context = httpx2.create_ssl_context(verify=verify, trust_env=trust_env)
        return AiohttpTransport(verify=context, limits=limits, proxy=proxy)


def build_ssl_context(
    *,
    verify_ssl_certs: bool = True,
    ssl_context: ssl.SSLContext | None = None,
    ca_bundle_file: str | None = None,
    cert_file: str | None = None,
    key_file: str | None = None,
    key_file_password: str | None = None,
    trust_env: bool = True,
    for_auth: bool = False,
    auth_ssl_context: ssl.SSLContext | None = None,
) -> ssl.SSLContext | bool:
    """Build a TLS context without modifying a caller-owned context."""
    selected = auth_ssl_context if for_auth and auth_ssl_context is not None else ssl_context
    client_cert = None if for_auth else cert_file
    if not for_auth and (key_file or key_file_password) and not cert_file:
        raise ValueError("key_file and key_file_password require cert_file")
    if selected is not None:
        if ca_bundle_file or client_cert or not verify_ssl_certs:
            raise ValueError("ssl_context cannot be combined with CA, client certificate, or verify_ssl_certs=False")
        return selected
    if ca_bundle_file and not verify_ssl_certs:
        raise ValueError("ca_bundle_file cannot be combined with verify_ssl_certs=False")
    if ca_bundle_file:
        context = ssl.create_default_context(cafile=ca_bundle_file)
    else:
        context = httpx2.create_ssl_context(verify=verify_ssl_certs, trust_env=trust_env)
    if client_cert:
        context.load_cert_chain(client_cert, key_file, key_file_password)
    return context
