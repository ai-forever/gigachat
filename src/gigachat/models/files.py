from typing import List, Optional

from gigachat.models.utils import WithXHeaders
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


class UploadedFiles(WithXHeaders):
    data: List[UploadedFile]
    """Список загруженных файлов"""


class DeletedFile(WithXHeaders):
    """Информация об удаленном файле"""

    id_: str = Field(alias="id")
    """Идентификатор файла """
    deleted: bool
    """Признак удаления файла"""


class Image(WithXHeaders):
    """Изображение"""

    content: str
    """Изображение в base64 кодировке"""
