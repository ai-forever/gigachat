from typing import Optional

from gigachat.models.function_call import FunctionCall
from gigachat.models.messages_role import MessagesRole
from gigachat.pydantic_v1 import BaseModel


class MessagesChunk(BaseModel):
    """Короткое сообщение"""

    role: Optional[MessagesRole] = None
    """Роль автора сообщения"""
    content: Optional[str] = None
    """Текст сообщения"""
    function_call: Optional[FunctionCall] = None
    """Вызов функции"""
