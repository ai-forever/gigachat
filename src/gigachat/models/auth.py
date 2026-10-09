from pydantic import Field, field_validator

from gigachat.models.base import APIResponse

# Unix time in milliseconds passed this value back in 1970, while unix time in seconds
# will only reach it in 2286. Anything below is therefore a second-based timestamp.
SECONDS_TO_MILLISECONDS_THRESHOLD = 10_000_000_000


class AccessToken(APIResponse):
    """Access token information."""

    access_token: str = Field(description="Generated Access Token.")
    expires_at: int = Field(description="Unix timestamp (in milliseconds) when the Access Token expires.")

    @field_validator("expires_at")
    @classmethod
    def _normalize_expires_at(cls, value: int) -> int:
        """Convert second-based expirations to milliseconds.

        Some authorization backends return the expiration in seconds. Zero is preserved:
        it marks a token that never expires.
        """
        if 0 < value < SECONDS_TO_MILLISECONDS_THRESHOLD:
            return value * 1000
        return value


class Token(APIResponse):
    """Raw token response."""

    tok: str = Field(description="Generated Access Token.")
    exp: int = Field(description="Unix timestamp (in seconds or milliseconds) when the Access Token expires.")
