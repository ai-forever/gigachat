from gigachat.models.with_x_headers import WithXHeaders


class Token(WithXHeaders):
    """Токен доступа"""

    tok: str
    """Сгенерированный Access Token"""
    exp: int
    """Unix-время завершения действия Access Token в миллисекундах"""
