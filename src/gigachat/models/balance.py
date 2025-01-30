from typing import List

from gigachat.models.with_x_headers import WithXHeaders
from gigachat.pydantic_v1 import BaseModel


class BalanceValue(BaseModel):
    """Баланс для услуги"""

    usage: str
    """Наименование услуги"""
    value: float
    """Количество доступных токенов"""


class Balance(WithXHeaders):
    """Текущий баланс"""

    balance: List[BalanceValue]
