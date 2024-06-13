from typing import List

from gigachat.models import ChoicesChunk
from gigachat.models.usage import Usage
from gigachat.pydantic_v1 import BaseModel, Field


class ThreadCompletionChunk(BaseModel):
    """Ответ модели"""

    object_: str = Field(alias="object")
    """Название вызываемого метода"""
    model: str
    """Название модели, которая вернула ответ"""
    thread_id: str
    """Идентификатор треда"""
    message_id: str
    """Идентификатор сообщения ответа модели"""
    created: int
    """Дата и время создания ответа в формате Unix time"""
    usage: Usage
    """Данные об использовании модели"""
    choices: List[ChoicesChunk]
    """Массив ответов модели в потоке"""
