from gigachat.models.with_x_headers import WithXHeaders
from gigachat.pydantic_v1 import Field


class DeletedFile(WithXHeaders):
    """Информация об удаленном файле"""

    id_: str = Field(alias="id")
    """Идентификатор файла """
    deleted: bool
    """Признак удаления файла"""
