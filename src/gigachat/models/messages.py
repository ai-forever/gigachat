from typing import Any, Optional

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
    id: Optional[Any] = None  # noqa: A003

    class Config:
        use_enum_values = True
