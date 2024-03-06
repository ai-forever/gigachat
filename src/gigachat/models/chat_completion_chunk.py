from typing import List

from gigachat.models.choices_chunk import ChoicesChunk
from gigachat.pydantic_v1 import BaseModel, Field


class ChatCompletionChunk(BaseModel):
    """Ответ модели в потоке"""

    choices: List[ChoicesChunk]
    """Массив ответов модели в потоке"""
    created: int
    """Дата и время создания ответа в формате Unix time"""
    model: str
    """Название модели, которая вернула ответ"""
    object_: str = Field(alias="object")
    """Название вызываемого метода"""
