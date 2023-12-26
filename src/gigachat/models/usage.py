from typing import Optional

from gigachat.pydantic_v1 import BaseModel


class Usage(BaseModel):
    """Данные об использовании модели"""

    prompt_tokens: Optional[int]
    """Количество токенов во входящем сообщении"""
    completion_tokens: Optional[int]
    """Количество токенов, сгенерированных моделью"""
    total_tokens: Optional[int]
    """Общее количество токенов"""
