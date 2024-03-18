from typing import Any, Dict, List, Optional

from gigachat.pydantic_v1 import BaseModel, Field


class FunctionParametersProperty(BaseModel):
    """Функция, которая может быть вызвана моделью"""

    type_: str = Field(default="object", alias="type")
    """Тип аргумента функции"""
    description: str = ""
    """Описание аргумента"""
    items: Optional[Dict[str, Any]] = None
    """Возможные значения аргумента"""
    enum: Optional[List[str]] = None
    """Возможные значения enum"""
    properties: Optional[Dict[Any, "FunctionParametersProperty"]] = None
