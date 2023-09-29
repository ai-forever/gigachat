from gigachat.pydantic_v1 import BaseModel


class Usage(BaseModel):
    """Данные об использовании модели"""

    prompt_tokens: int
    """Количество токенов во входящем сообщении"""
    completion_tokens: int
    """Количество токенов, сгенерированных моделью"""
    total_tokens: int
    """Общее количество токенов"""
