from typing import List, Literal, Optional

from gigachat.models.chat import Function
from gigachat.models.utils import WithXHeaders
from gigachat.pydantic_v1 import BaseModel, Field


class AICheckResult(BaseModel):
    """Ответ модели"""

    category: Literal["ai", "human", "mixed"]
    """Результат проверки текста. Возможные значения: [ai, human, mixed]"""
    characters: int
    """Количество символов в переданном тексте"""
    tokens: int
    """Количество токенов в переданном тексте"""
    ai_intervals: Optional[List[List[int]]]
    """
    Части текста, сгенерированные моделью.
    Обозначаются индексами символов, с которых начинаются и заканчиваются сгенерированные фрагменты.
    """


class BalanceValue(BaseModel):
    """Баланс для услуги"""

    usage: str
    """Наименование услуги"""
    value: float
    """Количество доступных токенов"""


class Balance(WithXHeaders):
    """Текущий баланс"""

    balance: List[BalanceValue]


class TokensCount(WithXHeaders):
    """Информация о количестве токенов"""

    tokens: int
    """Количество токенов в соответствующей строке."""
    characters: int
    """Количество токенов в соответствующей строке."""
    object_: str = Field(alias="object")
    """Тип сущности в ответе, например, список"""


class OpenApiFunctions(WithXHeaders):
    """Функции конвертированные из OpenAPI в GigaFunctions"""

    functions: List[Function]
    """Массив с функциями"""
