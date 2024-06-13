from gigachat.pydantic_v1 import BaseModel


class ThreadMessageAttachment(BaseModel):
    """Файл"""

    file_id: str
    """Индентификатор предзагруженного ранее файла"""
    name: str
    """Наименование файла"""
