import ssl
from typing import Literal

import httpx2
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "GIGACHAT_"

BASE_URL = "https://api.giga.chat/v1"
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
SCOPE = "GIGACHAT_API_PERS"


class Settings(BaseSettings):
    base_url: str = Field(
        default=BASE_URL,
        description="Address against which requests are executed.",
    )
    auth_url: str = Field(
        default=AUTH_URL,
        description="Address for requesting OAuth 2.0 access token.",
    )
    credentials: str | None = Field(
        default=None,
        description="Authorization data.",
    )
    scope: str = Field(
        default=SCOPE,
        description="API version to which access is provided.",
    )
    access_token: str | None = Field(
        default=None,
        description="JWE token.",
    )
    model: str | None = Field(
        default=None,
        description="Name of the model to receive a response from.",
    )
    session_id: str | None = Field(
        default=None,
        description="Default X-Session-ID header for API requests.",
    )
    profanity_check: bool | None = Field(
        default=None,
        description="Censorship parameter.",
    )

    user: str | None = Field(
        default=None,
        description="Username for basic authentication.",
    )
    password: str | None = Field(
        default=None,
        description="Password for basic authentication.",
    )

    timeout: float | httpx2.Timeout = Field(
        default=30.0,
        description="Request timeout in seconds.",
    )
    verify_ssl_certs: bool = Field(
        default=True,
        description="Verify server TLS certificates.",
    )

    ssl_context: ssl.SSLContext | None = Field(
        default=None,
        description="Custom SSL context.",
    )
    ca_bundle_file: str | None = Field(
        default=None,
        description="Path to CA bundle file for verifying TLS certificates.",
    )
    cert_file: str | None = Field(
        default=None,
        description="Path to client certificate file.",
    )
    key_file: str | None = Field(
        default=None,
        description="Path to client private key file.",
    )
    key_file_password: str | None = Field(
        default=None,
        description="Password for encrypted client private key file.",
    )
    flags: list[str] | None = Field(
        default=None,
        description="Additional flags to control client behavior.",
    )
    max_connections: int | None = Field(
        default=None,
        description="Maximum number of simultaneous connections to the GigaChat API.",
    )

    max_retries: int = Field(
        default=0,
        ge=0,
        description="Maximum number of retries for transient errors. Default is 0 (disabled).",
    )
    retry_backoff_factor: float = Field(
        default=0.5,
        description="Backoff factor for retry delays.",
    )
    retry_on_status_codes: tuple[int, ...] = Field(
        default=(429, 500, 502, 503, 504),
        description="HTTP status codes that trigger a retry.",
    )

    token_expiry_buffer_ms: int = Field(
        default=60000,
        description="Buffer time (ms) before token expiry to trigger refresh. Default is 60000 (60 seconds).",
    )

    max_retry_time: float = Field(default=60.0, gt=0, allow_inf_nan=False)
    max_sse_event_size: int = Field(default=1048576, gt=0)
    trust_env: bool = True
    proxy: str | None = None
    http2: bool = False
    limits: httpx2.Limits | None = None
    async_backend: Literal["httpx2", "aiohttp"] = "httpx2"
    auth_ssl_context: ssl.SSLContext | None = None

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
