from typing import List

from gigachat.pydantic_v1 import BaseModel


class BalanceValue(BaseModel):
    """Баланс для услуги"""

    usage: str
    """Наименование услуги"""
    value: float
    """Количество доступных токенов"""


class Balance(BaseModel):
    """Текущий баланс"""

    balance: List[BalanceValue]
