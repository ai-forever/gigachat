from gigachat.models.with_x_headers import WithXHeaders
from gigachat.pydantic_v1 import Field


class Model(WithXHeaders):
    """Описание модели"""

    id_: str = Field(alias="id")
    """Название модели"""
    object_: str = Field(alias="object")
    """Тип сущности в ответе, например, модель"""
    owned_by: str
    """Владелец модели"""
