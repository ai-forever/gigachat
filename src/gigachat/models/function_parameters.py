from typing import Any, Dict, List, Optional

from gigachat.pydantic_v1 import BaseModel, Field


class FunctionParameters(BaseModel):
    """Функция, которая может быть вызвана моделью"""

    _type: str = Field(default="obect", alias="type")
    """Тип параметров функции"""
    properties: Optional[Dict[Any, Any]] = None
    """Описание функции"""
    required: Optional[List[str]] = None
    """Список обязательных параметров"""
