"""Immutable per-call configuration and ordered option composition."""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import httpx2


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
