from typing import Optional

from gigachat.models.function_call import FunctionCall
from gigachat.models.messages_role import MessagesRole
from gigachat.pydantic_v1 import BaseModel


class Messages(BaseModel):
    """Сообщение"""

    role: MessagesRole
    """Роль автора сообщения"""
    content: str = ""
    """Текст сообщения"""
    function_call: Optional[FunctionCall] = None
    """Вызов функции"""

    class Config:
        use_enum_values = True
