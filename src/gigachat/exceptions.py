class GigaChatException(Exception):
    """Base exception for GigaChat library."""

    ...


class ResponseError(GigaChatException):
    """Exception raised when API response contains an error."""

    ...


class AuthenticationError(ResponseError):
    """Exception raised when authentication fails."""

    ...
