from typing import Any, Dict, List, Optional

from gigachat.models.few_shot_example import FewShotExample
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
    few_shot_examples: Optional[List[FewShotExample]] = None
    return_parameters: Optional[Dict[Any, Any]] = None
    """Список возвращаемых параметров функции"""
