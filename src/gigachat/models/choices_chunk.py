from typing import Optional

from gigachat.models.messages_chunk import MessagesChunk
from gigachat.pydantic_v1 import BaseModel


class ChoicesChunk(BaseModel):
    """Ответ модели в потоке"""

    delta: MessagesChunk
    """Короткое сообщение"""
    index: int
    """Индекс сообщения в массиве начиная с нуля"""
    finish_reason: Optional[str] = None
    """Причина завершения гипотезы"""
