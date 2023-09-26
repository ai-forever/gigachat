import logging
from typing import Any, Dict, Optional

from gigachat.pydantic_v1 import BaseSettings, root_validator

ENV_PREFIX = "GIGACHAT_"

# BASE_URL = "https://beta.saluteai.sberdevices.ru/v1"
BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
SCOPE = "GIGACHAT_API_CORP"


class Settings(BaseSettings):
    base_url: str = BASE_URL
    auth_url: str = AUTH_URL
    credentials: Optional[str] = None
    scope: str = SCOPE

    access_token: Optional[str] = None
    model: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None

    timeout: float = 30.0
    verify_ssl: bool = True

    use_auth: bool = True
    verbose: bool = False

    class Config:
        env_prefix = ENV_PREFIX

    @root_validator
    def check_credentials(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values["use_auth"]:
            use_secrets = values["credentials"] or values["access_token"] or (values["user"] and values["password"])
            if not use_secrets:
                logging.warning("Please provide GIGACHAT_CREDENTIALS environment variables.")

        return values
