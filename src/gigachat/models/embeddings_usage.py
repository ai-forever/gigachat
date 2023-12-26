from gigachat.pydantic_v1 import BaseModel


class EmbeddingsUsage(BaseModel):
    """Данные об использовании модели"""

    prompt_tokens: int
    """Количество токенов во входящем сообщении"""
