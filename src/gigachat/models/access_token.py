from gigachat.pydantic_v1 import BaseModel


class AccessToken(BaseModel):
    """Токен доступа"""

    access_token: str
    """Сгенерированный Access Token"""
    expires_at: int
    """Unix-время завершения действия Access Token в миллисекундах"""
