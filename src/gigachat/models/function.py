from typing import Any, Dict, Optional

from gigachat.models.function_parameters import FunctionParameters
from gigachat.pydantic_v1 import BaseModel


class Function(BaseModel):
    """Функция, которая может быть вызвана моделью"""

    name: str
    """Название функции"""
    description: Optional[str] = None
    """Описание функции"""
    parameters: Optional[FunctionParameters] = None
    """Список параметров функции"""
    return_parameters: Optional[Dict[Any, Any]] = None
    """Список возвращаемых параметров функции"""
