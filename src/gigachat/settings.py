from typing import Optional

from gigachat.pydantic_v1 import BaseSettings

ENV_PREFIX = "GIGACHAT_"

BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
SCOPE = "GIGACHAT_API_PERS"


class Settings(BaseSettings):
    base_url: str = BASE_URL
    """Адрес относительно которого выполняются запросы"""
    auth_url: str = AUTH_URL
    credentials: Optional[str] = None
    scope: str = SCOPE

    access_token: Optional[str] = None
    model: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None

    timeout: float = 30.0
    verify_ssl_certs: bool = True

    verbose: bool = False

    ca_bundle_file: Optional[str] = None
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    key_file_password: Optional[str] = None

    class Config:
        env_prefix = ENV_PREFIX
