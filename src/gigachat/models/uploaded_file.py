from typing import Optional

from gigachat.models.with_x_headers import WithXHeaders
from gigachat.pydantic_v1 import Field


class UploadedFile(WithXHeaders):
    """Информация о загруженном файле"""

    id_: str = Field(alias="id")
    """Идентификатор файла, на который можно ссылаться в API """
    object_: str = Field(alias="object")
    """Тип объекта"""
    bytes_: int = Field(alias="bytes")
    """Размер файла в байтах"""
    created_at: int
    """Время создания файла в Unix-time формате"""
    filename: str
    """Имя файла"""
    purpose: str
    """Предполагаемое назначение файла."""
    access_policy: Optional[str] = None
    """Доступность файла"""
