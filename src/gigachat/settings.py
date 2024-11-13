import ssl
from typing import List, Optional

from gigachat.pydantic_v1 import BaseSettings

ENV_PREFIX = "GIGACHAT_"

BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
SCOPE = "GIGACHAT_API_PERS"


class Settings(BaseSettings):
    base_url: str = BASE_URL
    """Адрес относительно которого выполняются запросы"""
    auth_url: str = AUTH_URL
    """Адрес для запроса токена доступа OAuth 2.0"""
    credentials: Optional[str] = None
    """Авторизационные данные"""
    scope: str = SCOPE
    """Версия API, к которой предоставляется доступ"""
    access_token: Optional[str] = None
    """JWE токен"""
    model: Optional[str] = None
    """Название модели, от которой нужно получить ответ"""
    profanity_check: Optional[bool] = None
    """Параметр цензуры"""

    user: Optional[str] = None
    password: Optional[str] = None

    timeout: float = 30.0
    verify_ssl_certs: bool = True

    verbose: bool = False

    ssl_context: Optional[ssl.SSLContext] = None
    ca_bundle_file: Optional[str] = None
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    key_file_password: Optional[str] = None
    flags: Optional[List[str]] = None

    class Config:
        env_prefix = ENV_PREFIX
