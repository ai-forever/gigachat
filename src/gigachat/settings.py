import ssl
from typing import List, Optional, Tuple

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "GIGACHAT_"

BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
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
    credentials: Optional[str] = Field(
        default=None,
        description="Authorization data.",
    )
    scope: str = Field(
        default=SCOPE,
        description="API version to which access is provided.",
    )
    access_token: Optional[str] = Field(
        default=None,
        description="JWE token.",
    )
    model: Optional[str] = Field(
        default=None,
        description="Name of the model to receive a response from.",
    )
    profanity_check: Optional[bool] = Field(
        default=None,
        description="Censorship parameter.",
    )

    user: Optional[str] = Field(
        default=None,
        description="Username for basic authentication.",
    )
    password: Optional[str] = Field(
        default=None,
        description="Password for basic authentication.",
    )

    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds.",
    )
    verify_ssl_certs: bool = Field(
        default=True,
        description="Verify server TLS certificates.",
    )

    ssl_context: Optional[ssl.SSLContext] = Field(
        default=None,
        description="Custom SSL context.",
    )
    ca_bundle_file: Optional[str] = Field(
        default=None,
        description="Path to CA bundle file for verifying TLS certificates.",
    )
    cert_file: Optional[str] = Field(
        default=None,
        description="Path to client certificate file.",
    )
    key_file: Optional[str] = Field(
        default=None,
        description="Path to client private key file.",
    )
    key_file_password: Optional[str] = Field(
        default=None,
        description="Password for encrypted client private key file.",
    )
    flags: Optional[List[str]] = Field(
        default=None,
        description="Additional flags to control client behavior.",
    )
    max_connections: Optional[int] = Field(
        default=None,
        description="Maximum number of simultaneous connections to the GigaChat API.",
    )

    max_retries: int = Field(
        default=0,
        description="Maximum number of retries for transient errors. Default is 0 (disabled).",
    )
    retry_backoff_factor: float = Field(
        default=0.5,
        description="Backoff factor for retry delays.",
    )
    retry_on_status_codes: Tuple[int, ...] = Field(
        default=(429, 500, 502, 503, 504),
        description="HTTP status codes that trigger a retry.",
    )

    token_expiry_buffer_ms: int = Field(
        default=60000,
        description="Buffer time (ms) before token expiry to trigger refresh. Default is 60000 (60 seconds).",
    )

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
