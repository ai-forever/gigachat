from gigachat.models.utils import WithXHeaders


class AccessToken(WithXHeaders):
    """Токен доступа"""

    access_token: str
    """Сгенерированный Access Token"""
    expires_at: int
    """Unix-время завершения действия Access Token в миллисекундах"""


class Token(WithXHeaders):
    """Токен доступа"""

    tok: str
    """Сгенерированный Access Token"""
    exp: int
    """Unix-время завершения действия Access Token в миллисекундах"""
