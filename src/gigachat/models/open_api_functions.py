from typing import List

from gigachat.models.function import Function
from gigachat.models.with_x_headers import WithXHeaders


class OpenApiFunctions(WithXHeaders):
    """Функции конвертированные из OpenAPI в GigaFunctions"""

    functions: List[Function]
    """Массив с функциями"""
