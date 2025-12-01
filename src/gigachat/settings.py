import ssl
from typing import List, Optional, Tuple

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "GIGACHAT_"

BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
SCOPE = "GIGACHAT_API_PERS"


class Settings(BaseSettings):
    base_url: str = BASE_URL
    """Address against which requests are executed."""
    auth_url: str = AUTH_URL
    """Address for requesting OAuth 2.0 access token."""
    credentials: Optional[str] = None
    """Authorization data."""
    scope: str = SCOPE
    """API version to which access is provided."""
    access_token: Optional[str] = None
    """JWE token."""
    model: Optional[str] = None
    """Name of the model to receive a response from."""
    profanity_check: Optional[bool] = None
    """Censorship parameter."""

    user: Optional[str] = None
    password: Optional[str] = None

    timeout: float = 30.0
    verify_ssl_certs: bool = True

    ssl_context: Optional[ssl.SSLContext] = None
    ca_bundle_file: Optional[str] = None
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    key_file_password: Optional[str] = None
    flags: Optional[List[str]] = None
    max_connections: Optional[int] = None
    """Maximum number of simultaneous connections to the GigaChat API."""

    max_retries: int = 0
    """Maximum number of retries for transient errors. Default is 0 (disabled)."""
    retry_backoff_factor: float = 0.5
    """Backoff factor for retry delays."""
    retry_on_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504)
    """HTTP status codes that trigger a retry."""

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
