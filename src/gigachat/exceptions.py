import math
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, Union

import httpx2 as httpx

if TYPE_CHECKING:
    from gigachat.models.chat import ChatCompletion
    from gigachat.models.chat_completions import ChatCompletionResponse

__all__ = [
    "GigaChatException",
    "ResponseError",
    "BadRequestError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "RequestEntityTooLargeError",
    "UnprocessableEntityError",
    "RateLimitError",
    "ServerError",
    "LengthFinishReasonError",
    "ModelNotSpecifiedError",
]


class GigaChatException(Exception):
    """Base exception for GigaChat library."""


class ResponseError(GigaChatException):
    """Exception raised when API response contains an error."""

    def __init__(
        self,
        url: httpx.URL | str,
        status_code: int,
        content: bytes | None,
        headers: httpx.Headers | None,
    ) -> None:
        self.url = url
        self.status_code = status_code
        self.content = content
        self.headers = headers
        super().__init__(f"{status_code} {url}")

    def __str__(self) -> str:
        content = self.content.decode("utf-8", errors="replace") if self.content is not None else None
        return f"{self.status_code} {self.url}: {content!r}, {self.headers!r}"

    @property
    def request_id(self) -> str | None:
        return self.headers.get("x-request-id") if self.headers else None

    @property
    def retry_after(self) -> float:
        return parse_retry_after(self.headers.get("retry-after")) if self.headers else 0.0


class BadRequestError(ResponseError):
    """Exception raised for 400 Bad Request."""


class AuthenticationError(ResponseError):
    """Exception raised when authentication fails (401 Unauthorized)."""


class ForbiddenError(ResponseError):
    """Exception raised for 403 Forbidden."""


class NotFoundError(ResponseError):
    """Exception raised for 404 Not Found."""


class RequestEntityTooLargeError(ResponseError):
    """Exception raised for 413 Request Entity Too Large."""


class UnprocessableEntityError(ResponseError):
    """Exception raised for 422 Unprocessable Entity."""


class RateLimitError(ResponseError):
    """Exception raised for 429 Too Many Requests."""


class ServerError(ResponseError):
    """Exception raised for 5xx Server Errors."""


class LengthFinishReasonError(GigaChatException):
    """Exception raised when finish_reason is 'length' (response truncated)."""

    def __init__(self, completion: Union["ChatCompletion", "ChatCompletionResponse"]) -> None:
        self.completion = completion
        super().__init__("Could not parse response content as the length limit was reached")


class ModelNotSpecifiedError(GigaChatException):
    """Exception raised when no model is specified for a request."""

    def __init__(self) -> None:
        super().__init__(
            "No model specified. Pass `model` in the request payload, "
            "set `GigaChat(model=...)` or the GIGACHAT_MODEL environment variable. "
            "Use `get_models()` to list available models."
        )


def parse_retry_after(value: str | None) -> float:
    """Parse finite seconds or an HTTP date without shortening server waits."""
    if not value:
        return 0.0
    try:
        delay = float(value)
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            delay = (date - datetime.now(timezone.utc)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return 0.0
    return delay if math.isfinite(delay) and delay > 0 else 0.0


class APIConnectionError(GigaChatException):
    """Report an HTTP transport failure with its original exception as cause."""

    def __init__(self, message: str = "Connection failed", *, request_id: str | None = None) -> None:
        self.request_id = request_id
        super().__init__(message)


class APITimeoutError(APIConnectionError):
    """Report a network timeout."""


class APIResponseValidationError(GigaChatException):
    """Report a server response that violates the expected schema."""

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        self.request_id = request_id
        super().__init__(message)


class StreamInterruptedError(APIConnectionError):
    """Report an interrupted stream without replaying already delivered output."""

    def __init__(
        self, message: str = "Stream interrupted", *, request_id: str | None = None, partial_output: bool = False
    ) -> None:
        self.partial_output = partial_output
        super().__init__(message, request_id=request_id)
