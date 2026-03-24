from pydantic import Field, SecretStr

from gigachat.models.base import APIResponse


class AccessToken(APIResponse):
    """Access token information."""

    access_token: SecretStr = Field(description="Generated Access Token.")
    expires_at: int = Field(description="Unix timestamp (in milliseconds) when the Access Token expires.")


class Token(APIResponse):
    """Raw token response."""

    tok: SecretStr = Field(description="Generated Access Token.")
    exp: int = Field(description="Unix timestamp (in milliseconds) when the Access Token expires.")
