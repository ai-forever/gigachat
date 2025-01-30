from gigachat.models.with_x_headers import WithXHeaders
from gigachat.pydantic_v1 import Field


class TokensCount(WithXHeaders):
    """Информация о количестве токенов"""

    tokens: int
    """Количество токенов в соответствующей строке."""
    characters: int
    """Количество токенов в соответствующей строке."""
    object_: str = Field(alias="object")
    """Тип сущности в ответе, например, список"""
