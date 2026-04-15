from typing import Type

import httpx
import pytest

from gigachat.api.utils import _raise_for_status
from gigachat.exceptions import (
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    LengthFinishReasonError,
    NotFoundError,
    RateLimitError,
    RequestEntityTooLargeError,
    ResponseError,
    ServerError,
    UnprocessableEntityError,
)


def test_response_error_init() -> None:
    url = "http://example.com"
    status_code = 400
    content = b"error"
    headers = httpx.Headers({"x-request-id": "123"})

    exc = ResponseError(url, status_code, content, headers)

    assert exc.url == url
    assert exc.status_code == status_code
    assert exc.content == content
    assert exc.headers == headers
    assert str(exc) == "400 http://example.com: b'error', Headers({'x-request-id': '123'})"


def test_rate_limit_retry_after() -> None:
    headers = httpx.Headers({"retry-after": "60"})
    exc = RateLimitError("url", 429, b"", headers)
    assert exc.retry_after == 60.0


def test_rate_limit_retry_after_float() -> None:
    headers = httpx.Headers({"retry-after": "1.5"})
    exc = RateLimitError("url", 429, b"", headers)
    assert exc.retry_after == 1.5


def test_rate_limit_retry_after_missing() -> None:
    exc = RateLimitError("url", 429, b"", httpx.Headers())
    assert exc.retry_after == 0.0


def test_rate_limit_retry_after_invalid() -> None:
    headers = httpx.Headers({"retry-after": "invalid"})
    exc = RateLimitError("url", 429, b"", headers)
    assert exc.retry_after == 0.0


def test_rate_limit_retry_after_none_headers() -> None:
    exc = RateLimitError("url", 429, b"", None)
    assert exc.retry_after == 0.0


def test_length_finish_reason_error_message() -> None:
    completion = object()
    exc = LengthFinishReasonError(completion=completion)  # type: ignore[arg-type]
    assert exc.completion is completion
    assert str(exc) == "Could not parse response content as the length limit was reached"


@pytest.mark.parametrize(
    ("status_code", "expected_exception"),
    [
        (400, BadRequestError),
        (401, AuthenticationError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (413, RequestEntityTooLargeError),
        (422, UnprocessableEntityError),
        (429, RateLimitError),
        (500, ServerError),
        (418, ResponseError),  # Default
    ],
)
def test_raise_for_status_mapping(status_code: int, expected_exception: Type[ResponseError]) -> None:
    url = "http://example.com"
    content = b"error"
    headers = httpx.Headers()

    with pytest.raises(expected_exception) as exc_info:
        _raise_for_status(url, status_code, content, headers)

    assert exc_info.value.status_code == status_code
