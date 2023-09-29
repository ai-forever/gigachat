from typing import List

from gigachat.models.model import Model
from gigachat.pydantic_v1 import BaseModel, Field


class Models(BaseModel):
    """Доступные модели"""

    data: List[Model]
    """Массив объектов с данными доступных моделей"""
    object_: str = Field(alias="object")
    """Тип сущности в ответе, например, список"""
