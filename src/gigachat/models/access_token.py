from gigachat.models.with_x_headers import WithXHeaders


class AccessToken(WithXHeaders):
    """Токен доступа"""

    access_token: str
    """Сгенерированный Access Token"""
    expires_at: int
    """Unix-время завершения действия Access Token в миллисекундах"""
