from gigachat.pydantic_v1 import BaseModel


class Token(BaseModel):
    """Токен доступа"""

    tok: str
    """Сгенерированный Access Token"""
    exp: int
    """Unix-время завершения действия Access Token в миллисекундах"""
