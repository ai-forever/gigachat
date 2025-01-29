from typing import List

from gigachat.models.model import Model
from gigachat.models.with_x_headers import WithXHeaders
from gigachat.pydantic_v1 import Field


class Models(WithXHeaders):
    """Доступные модели"""

    data: List[Model]
    """Массив объектов с данными доступных моделей"""
    object_: str = Field(alias="object")
    """Тип сущности в ответе, например, список"""
