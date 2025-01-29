from typing import List

from gigachat.models.choices import Choices
from gigachat.models.usage import Usage
from gigachat.models.with_x_headers import WithXHeaders
from gigachat.pydantic_v1 import Field


class ChatCompletion(WithXHeaders):
    """Ответ модели"""

    choices: List[Choices]
    """Массив ответов модели"""
    created: int
    """Дата и время создания ответа в формате Unix time"""
    model: str
    """Название модели, которая вернула ответ"""
    usage: Usage
    """Данные об использовании модели"""
    object_: str = Field(alias="object")
    """Название вызываемого метода"""
