from typing import Optional

from gigachat.models.messages import Messages
from gigachat.pydantic_v1 import BaseModel


class Choices(BaseModel):
    """Ответ модели"""

    message: Messages
    """Сгенерированное сообщение"""
    index: int
    """Индекс сообщения в массиве начиная с нуля"""
    finish_reason: Optional[str] = None
    """Причина завершения гипотезы"""
