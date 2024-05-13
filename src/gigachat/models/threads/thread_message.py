from typing import List, Optional

from gigachat.models.function_call import FunctionCall
from gigachat.models.messages_role import MessagesRole
from gigachat.models.threads.thread_message_attachment import ThreadMessageAttachment
from gigachat.pydantic_v1 import BaseModel


class ThreadMessage(BaseModel):
    """Сообщение"""

    message_id: str
    """Идентификатор сообщения"""
    role: MessagesRole
    """Роль автора сообщения"""
    content: str = ""
    """Текст сообщения"""
    attachments: Optional[List[ThreadMessageAttachment]] = []
    """Идентификаторы предзагруженных ранее файлов"""
    created_at: int
    """Дата создания сообщения в Unix-time формате"""
    function_call: Optional[FunctionCall] = None
    """Вызов функции"""
    finish_reason: Optional[str] = None
    """Причина завершения гипотезы"""

    class Config:
        use_enum_values = True
