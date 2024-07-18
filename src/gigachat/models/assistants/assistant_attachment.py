from gigachat.pydantic_v1 import BaseModel


class AssistantAttachment(BaseModel):
    """Файл"""

    file_id: str
    """Идентификатор файла прикрепленного к ассистенту"""
    name: str
    """Имя файла прикрепленного к ассистенту"""
