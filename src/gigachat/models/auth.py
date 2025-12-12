from gigachat.models.base import APIResponse


class AccessToken(APIResponse):
    """Access token information."""

    access_token: str
    """Generated Access Token."""
    expires_at: int
    """Unix timestamp (in milliseconds) when the Access Token expires."""


class Token(APIResponse):
    """Raw token response."""

    tok: str
    """Generated Access Token."""
    exp: int
    """Unix timestamp (in milliseconds) when the Access Token expires."""
