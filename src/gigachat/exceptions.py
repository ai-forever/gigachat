from typing import Optional, Union

import httpx

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
    "ContentParseError",
    "ContentValidationError",
    "LengthFinishReasonError",
    "ContentFilterFinishReasonError",
]


class GigaChatException(Exception):
    """Base exception for GigaChat library."""


class ResponseError(GigaChatException):
    """Exception raised when API response contains an error."""

    def __init__(
        self,
        url: Union[httpx.URL, str],
        status_code: int,
        content: Optional[bytes],
        headers: Optional[httpx.Headers],
    ) -> None:
        self.url = url
        self.status_code = status_code
        self.content = content
        self.headers = headers
        super().__init__(f"{status_code} {url}")

    def __str__(self) -> str:
        return f"{self.status_code} {self.url}: {self.content!r}, {self.headers!r}"


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

    @property
    def retry_after(self) -> float:
        """Return the number of seconds to wait before retrying."""
        if self.headers:
            retry_after = self.headers.get("retry-after")
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass
        return 0.0


class ServerError(ResponseError):
    """Exception raised for 5xx Server Errors."""


class ContentParseError(GigaChatException):
    """Exception raised when model response content is not valid JSON."""

    def __init__(self, content: str, completion: "ChatCompletion") -> None:
        self.content = content
        self.completion = completion
        super().__init__(f"Failed to parse response content as JSON: {content!r:.200}")


class ContentValidationError(GigaChatException):
    """Exception raised when parsed JSON does not match the expected model schema."""

    def __init__(self, content: str, completion: "ChatCompletion", cause: Exception) -> None:
        self.content = content
        self.completion = completion
        self.cause = cause
        super().__init__(f"Response JSON does not match the expected schema: {cause}")


class LengthFinishReasonError(GigaChatException):
    """Exception raised when finish_reason is 'length' (response truncated)."""

    def __init__(self, completion: "ChatCompletion") -> None:
        self.completion = completion
        super().__init__("Response was truncated (finish_reason='length'); JSON may be incomplete")


class ContentFilterFinishReasonError(GigaChatException):
    """Exception raised when finish_reason is 'content_filter'."""

    def __init__(self, completion: "ChatCompletion") -> None:
        self.completion = completion
        super().__init__("Response was filtered (finish_reason='content_filter')")
