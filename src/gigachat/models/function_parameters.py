from typing import Any, Dict, List, Optional

from gigachat.models.function_parameters_property import FunctionParametersProperty
from gigachat.pydantic_v1 import BaseModel, Field


class FunctionParameters(BaseModel):
    """Функция, которая может быть вызвана моделью"""

    type_: str = Field(default="object", alias="type")
    """Тип параметров функции"""
    properties: Optional[Dict[Any, FunctionParametersProperty]] = None
    """Описание функции"""
    required: Optional[List[str]] = None
    """Список обязательных параметров"""
