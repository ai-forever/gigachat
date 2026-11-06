"""Shared configuration, token state and lightweight client views."""

import asyncio
import copy
import logging
import ssl
import threading
import time
from typing import Any, Literal

import httpx2 as httpx
from typing_extensions import Self

from gigachat._http_client import DefaultAioHttpClient
from gigachat._request_options import RequestOptions
from gigachat.models.auth import AccessToken
from gigachat.settings import Settings

logger = logging.getLogger(__name__)


class _BaseClient:
    _access_token: AccessToken | None = None

    def __init__(
        self,
        *,
        base_url: str | None = None,
        auth_url: str | None = None,
        credentials: str | None = None,
        scope: str | None = None,
        access_token: str | None = None,
        model: str | None = None,
        session_id: str | None = None,
        profanity_check: bool | None = None,
        user: str | None = None,
        password: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        verify_ssl_certs: bool | None = None,
        ca_bundle_file: str | None = None,
        cert_file: str | None = None,
        key_file: str | None = None,
        key_file_password: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
        flags: list[str] | None = None,
        max_connections: int | None = None,
        max_retries: int | None = None,
        retry_backoff_factor: float | None = None,
        retry_on_status_codes: tuple[int, ...] | None = None,
        http_client: httpx.Client | None = None,
        async_http_client: httpx.AsyncClient | None = None,
        auth_http_client: httpx.Client | None = None,
        auth_async_http_client: httpx.AsyncClient | None = None,
        async_backend: Literal["httpx2", "aiohttp"] | None = None,
        trust_env: bool | None = None,
        proxy: str | None = None,
        http2: bool | None = None,
        limits: httpx.Limits | None = None,
        auth_ssl_context: ssl.SSLContext | None = None,
        max_retry_time: float | None = None,
        max_sse_event_size: int | None = None,
        token_expiry_buffer_ms: int | None = None,
        **_unknown_kwargs: Any,
    ) -> None:
        if _unknown_kwargs:
            logger.warning("GigaChat: unknown kwargs - %s", sorted(_unknown_kwargs))

        kwargs: dict[str, Any] = {
            "trust_env": trust_env,
            "proxy": proxy,
            "http2": http2,
            "limits": limits,
            "async_backend": async_backend,
            "auth_ssl_context": auth_ssl_context,
            "max_retry_time": max_retry_time,
            "max_sse_event_size": max_sse_event_size,
            "token_expiry_buffer_ms": token_expiry_buffer_ms,
            "base_url": base_url,
            "auth_url": auth_url,
            "credentials": credentials,
            "scope": scope,
            "access_token": access_token,
            "model": model,
            "session_id": session_id,
            "profanity_check": profanity_check,
            "user": user,
            "password": password,
            "timeout": timeout,
            "verify_ssl_certs": verify_ssl_certs,
            "ca_bundle_file": ca_bundle_file,
            "cert_file": cert_file,
            "key_file": key_file,
            "key_file_password": key_file_password,
            "ssl_context": ssl_context,
            "flags": flags,
            "max_connections": max_connections,
            "max_retries": max_retries,
            "retry_backoff_factor": retry_backoff_factor,
            "retry_on_status_codes": retry_on_status_codes,
        }
        for name, value, expected in (
            ("http_client", http_client, httpx.Client),
            ("auth_http_client", auth_http_client, httpx.Client),
            ("async_http_client", async_http_client, httpx.AsyncClient),
            ("auth_async_http_client", auth_async_http_client, httpx.AsyncClient),
            ("limits", limits, httpx.Limits),
        ):
            if value is not None and not isinstance(value, expected):
                raise TypeError(f"{name} must use httpx2 types, not legacy httpx")
        if timeout is not None and not isinstance(timeout, (int, float, httpx.Timeout)):
            raise TypeError("timeout must use httpx2.Timeout, not legacy httpx")
        if async_backend is not None:
            for supplied in (async_http_client, auth_async_http_client):
                if supplied is not None and (
                    isinstance(supplied, DefaultAioHttpClient) != (async_backend == "aiohttp")
                ):
                    raise ValueError("async_backend conflicts with the injected async client")
        self._owner = self
        self._closed = False
        self._sync_closed = False
        self._async_closed = False
        self._view_closed = False
        self._lifecycle_lock = threading.RLock()
        self._async_loop: asyncio.AbstractEventLoop | None = None
        self._request_options = RequestOptions()
        self._token_state_lock = threading.RLock()
        self._token_generation = 0
        self._access_token = None
        self._sync_token_lock = threading.RLock()
        self._async_token_lock = asyncio.Lock()
        self._client_instance: httpx.Client | None = http_client
        self._auth_client_instance: httpx.Client | None = auth_http_client
        self._aclient_instance: httpx.AsyncClient | None = async_http_client
        self._auth_aclient_instance: httpx.AsyncClient | None = auth_async_http_client
        self._injected_http = http_client
        self._injected_async_http = async_http_client
        self._injected_auth_http = auth_http_client
        self._injected_auth_async_http = auth_async_http_client
        config = {k: v for k, v in kwargs.items() if v is not None}
        self._settings = Settings(**config)
        if self._settings.access_token:
            self._access_token = AccessToken(access_token=self._settings.access_token, expires_at=0)

    @property
    def token(self) -> str | None:
        if self._owner._access_token:
            return self._owner._access_token.access_token
        else:
            return None

    @property
    def _use_auth(self) -> bool:
        return bool(self._settings.credentials or (self._settings.user and self._settings.password))

    def _is_token_usable(self) -> bool:
        """Check shared token expiry under the token-state lock."""
        with self._owner._token_state_lock:
            token = self._owner._access_token
            return token is not None and (
                token.expires_at == 0 or token.expires_at > time.time() * 1000 + self._settings.token_expiry_buffer_ms
            )

    def _reset_token(self, generation: int | None = None) -> None:
        """Invalidate only the generation used by the rejected request."""
        with self._owner._token_state_lock:
            if generation is None or generation == self._owner._token_generation:
                self._owner._access_token = None

    def _set_token(self, token: AccessToken) -> None:
        with self._owner._token_state_lock:
            self._owner._access_token = token
            self._owner._token_generation += 1

    def _ensure_open(self, side: str | None = None) -> None:
        if self._view_closed or self._owner._closed:
            raise RuntimeError("GigaChat client is closed")
        if side == "sync" and self._owner._sync_closed:
            raise RuntimeError("GigaChat synchronous client is closed")
        if side == "async" and self._owner._async_closed:
            raise RuntimeError("GigaChat asynchronous client is closed")

    def _ensure_async_loop(self) -> None:
        self._ensure_open("async")
        loop = asyncio.get_running_loop()
        with self._owner._lifecycle_lock:
            if self._owner._async_loop is None:
                self._owner._async_loop = loop
            elif self._owner._async_loop is not loop:
                raise RuntimeError("GigaChat async client cannot be used from a different event loop")

    def with_options(self, **kwargs: Any) -> Self:
        """Return a lightweight view sharing this client's token and HTTP pools."""
        self._ensure_open()
        view = copy.copy(self)
        view._request_options = self._request_options.merge(RequestOptions(**kwargs))
        for name in ("chat", "achat", "assistants", "threads", "a_assistants", "a_threads"):
            view.__dict__.pop(name, None)
        return view
