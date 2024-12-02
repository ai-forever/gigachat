from typing import List

from gigachat.models import Function
from gigachat.pydantic_v1 import BaseModel


class OpenApiFunctions(BaseModel):
    """Функции конвертированные из OpenAPI в GigaFunctions"""

    functions: List[Function]
    """Массив с функциями"""
