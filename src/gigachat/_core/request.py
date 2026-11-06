"""Immutable per-call configuration and ordered option composition."""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import IO, Any

import httpx2

from gigachat.context import (
    agent_id_cvar,
    authorization_cvar,
    client_id_cvar,
    custom_headers_cvar,
    operation_id_cvar,
    request_id_cvar,
    service_id_cvar,
    session_id_cvar,
    trace_id_cvar,
)


class NotGiven:
    """Represent an inherited option, distinct from explicit None."""

    def __copy__(self) -> NotGiven:
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> NotGiven:
        return self


NOT_GIVEN = NotGiven()


@dataclass(frozen=True, init=False)
class RequestOptions:
    """Snapshot per-request overrides; exposed containers are defensive copies."""

    timeout: float | httpx2.Timeout | None | NotGiven
    max_retries: int | NotGiven
    max_retry_time: float | NotGiven
    max_sse_event_size: int | NotGiven
    _headers: tuple[tuple[str, str], ...]
    _query: tuple[tuple[str, str], ...]
    _body: dict[str, Any]

    def __init__(
        self,
        *,
        timeout: float | httpx2.Timeout | None | NotGiven = NOT_GIVEN,
        max_retries: int | NotGiven = NOT_GIVEN,
        max_retry_time: float | NotGiven = NOT_GIVEN,
        max_sse_event_size: int | NotGiven = NOT_GIVEN,
        extra_headers: Mapping[str, str] | None = None,
        extra_query: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        extra_body: Mapping[str, Any] | None = None,
    ) -> None:
        if not isinstance(timeout, (NotGiven, httpx2.Timeout, float, int, type(None))):
            raise TypeError("timeout must use httpx2.Timeout, not legacy httpx.Timeout")
        if not isinstance(max_retries, NotGiven) and (not isinstance(max_retries, int) or max_retries < 0):
            raise ValueError("max_retries must be a nonnegative integer")
        if not isinstance(max_retry_time, NotGiven) and (not math.isfinite(max_retry_time) or max_retry_time <= 0):
            raise ValueError("max_retry_time must be finite and positive")
        if not isinstance(max_sse_event_size, NotGiven) and max_sse_event_size <= 0:
            raise ValueError("max_sse_event_size must be positive")
        for name, value in (
            ("timeout", timeout),
            ("max_retries", max_retries),
            ("max_retry_time", max_retry_time),
            ("max_sse_event_size", max_sse_event_size),
        ):
            object.__setattr__(self, name, copy.deepcopy(value))
        object.__setattr__(self, "_headers", tuple(httpx2.Headers(extra_headers or {}).multi_items()))
        object.__setattr__(
            self,
            "_query",
            tuple(
                httpx2.QueryParams(
                    dict(extra_query) if isinstance(extra_query, Mapping) else list(extra_query or [])
                ).multi_items()
            ),
        )
        object.__setattr__(self, "_body", copy.deepcopy(dict(extra_body or {})))

    @property
    def extra_headers(self) -> dict[str, str]:
        return dict(self._headers)

    @property
    def extra_query(self) -> list[tuple[str, str]]:
        return list(self._query)

    @property
    def extra_body(self) -> dict[str, Any]:
        return copy.deepcopy(self._body)

    def merge(self, other: RequestOptions | None) -> RequestOptions:
        if other is None:
            return self
        values = {
            name: getattr(self, name) if isinstance(getattr(other, name), NotGiven) else getattr(other, name)
            for name in ("timeout", "max_retries", "max_retry_time", "max_sse_event_size")
        }
        return RequestOptions(
            **values,
            extra_headers={**self.extra_headers, **other.extra_headers},
            extra_query=self.extra_query + other.extra_query,
            extra_body={**self.extra_body, **other.extra_body},
        )


FileContent = IO[bytes] | bytes | str
FileTypes = (
    FileContent
    | tuple[str | None, FileContent]
    | tuple[str | None, FileContent, str | None]
    | tuple[str | None, FileContent, str | None, Mapping[str, str]]
)


class OffsetFile:
    """Expose the caller's current position as the multipart file origin."""

    def __init__(self, file: Any, offset: int) -> None:
        self.file = file
        self.offset = offset
        self.name = getattr(file, "name", "upload")

    def read(self, size: int = -1) -> bytes:
        return bytes(self.file.read(size))

    def tell(self) -> int:
        return int(self.file.tell()) - self.offset

    def seek(self, offset: int, whence: int = 0) -> int:
        position = self.file.seek(offset + self.offset if whence == 0 else offset, whence)
        return int(position) - self.offset


class BodyReplay:
    def __init__(self, kwargs: dict[str, Any]) -> None:
        self.files: list[tuple[Any, int]] = []
        self.replayable = True
        files = dict(kwargs.get("files") or {})
        if files:
            kwargs["files"] = files
        for name, item in files.items():
            body = item[1] if isinstance(item, tuple) else item
            if isinstance(body, (str, bytes)):
                continue
            try:
                if not body.seekable():
                    self.replayable = False
                    continue
                offset = body.tell()
                body.seek(offset)
                self.files.append((body, offset))
                wrapped = OffsetFile(body, offset)
                files[name] = (item[0], wrapped, *item[2:]) if isinstance(item, tuple) else wrapped
            except (AttributeError, OSError, ValueError):
                self.replayable = False
        content = kwargs.get("content")
        if content is not None and not isinstance(content, (str, bytes)):
            self.replayable = False

    def rewind(self) -> None:
        for body, offset in self.files:
            body.seek(offset)


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


USER_AGENT = "GigaChat-python-lib"


def build_headers(access_token: str | None = None) -> dict[str, str]:
    """Build headers for the request."""
    headers = httpx2.Headers()

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    headers["User-Agent"] = USER_AGENT

    context_vars = {
        "Authorization": authorization_cvar,
        "X-Session-ID": session_id_cvar,
        "X-Request-ID": request_id_cvar,
        "X-Service-ID": service_id_cvar,
        "X-Operation-ID": operation_id_cvar,
        "X-Client-ID": client_id_cvar,
        "X-Trace-ID": trace_id_cvar,
        "X-Agent-ID": agent_id_cvar,
    }

    for header, cvar in context_vars.items():
        value = cvar.get()
        if value:
            headers[header] = value

    custom_headers = custom_headers_cvar.get()
    if custom_headers:
        headers.update(custom_headers)
    canonical = {name.lower(): name for name in ("User-Agent", *context_vars)}
    return {
        canonical.get(key.decode().lower(), key.decode()): value.decode(headers.encoding) for key, value in headers.raw
    }
