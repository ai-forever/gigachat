from typing import List

from gigachat.models.usage import Usage
from gigachat.pydantic_v1 import BaseModel, Field


class Embedding(BaseModel):
    """Ответ модели"""

    embedding: List[float]
    """Эмбеддинг"""
    usage: Usage
    """Данные об использовании модели"""
    index: int
    """Индекс эмбеддинга в массиве"""
    object_: str = Field(alias="object")
    """Название объекта"""
