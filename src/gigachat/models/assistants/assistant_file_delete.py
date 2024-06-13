from gigachat.pydantic_v1 import BaseModel


class AssistantFileDelete(BaseModel):
    """Информация об удаленном файле"""

    file_id: str
    """Идентификатор прикрепленного к ассистенту файла"""
    deleted: bool
    """Признак удаления. Если true - файл удален из ассистента"""
