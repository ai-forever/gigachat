from gigachat.models import Messages
from gigachat.models.usage import Usage
from gigachat.pydantic_v1 import BaseModel, Field


class ThreadCompletion(BaseModel):
    """Ответ модели"""

    object_: str = Field(alias="object")
    """Название вызываемого метода"""
    model: str
    """Название модели, которая вернула ответ"""
    thread_id: str
    """Идентификатор треда"""
    message_id: str
    """Идентификатор сообщения ответа модели"""
    created: int
    """Дата и время создания ответа в формате Unix time"""
    usage: Usage
    """Данные об использовании модели"""
    message: Messages
    """Массив ответов модели"""
    finish_reason: str
    """Причина завершения гипотезы"""
