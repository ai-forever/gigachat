from typing import List, Optional

from gigachat.models.choices_chunk import ChoicesChunk
from gigachat.models.usage import Usage
from gigachat.models.with_x_headers import WithXHeaders
from gigachat.pydantic_v1 import Field


class ChatCompletionChunk(WithXHeaders):
    """Ответ модели в потоке"""

    choices: List[ChoicesChunk]
    """Массив ответов модели в потоке"""
    created: int
    """Дата и время создания ответа в формате Unix time"""
    model: str
    """Название модели, которая вернула ответ"""
    object_: str = Field(alias="object")
    """Наименование вызываемого метода"""
    usage: Optional[Usage] = None
    """Данные о потребленных токенах"""
