"""HTTPX2 client defaults and the optional aiohttp transport."""

import math
import ssl
from typing import Any

import httpx2

from ._tls import build_ssl_context


def _aiohttp_timeout(value: Any) -> httpx2.Timeout:
    timeout = (
        httpx2.Timeout(value, write=None) if value is None or isinstance(value, (float, int)) else httpx2.Timeout(value)
    )
    for name, budget in timeout.as_dict().items():
        if budget is not None and (not math.isfinite(budget) or budget <= 0):
            raise ValueError(f"aiohttp {name} timeout must be finite and positive, or None to disable")
    if timeout.write is not None:
        raise ValueError("aiohttp transport does not support a separate write timeout")
    if timeout.connect is not None and timeout.pool is not None and timeout.connect != timeout.pool:
        raise ValueError("aiohttp transport requires equal connect and pool timeouts when both are set")
    return timeout


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
        from ._vendor.httpx_aiohttp.transport import AiohttpTransport

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
        from ._vendor.httpx_aiohttp.transport import AiohttpTransport

        if limits is None:
            raise ValueError("limits must be configured")
        if proxy.url.scheme not in ("http", "https"):
            raise ValueError("aiohttp transport supports only HTTP and HTTPS proxies")
        context = httpx2.create_ssl_context(verify=verify, trust_env=trust_env)
        return AiohttpTransport(verify=context, limits=limits, proxy=proxy)
