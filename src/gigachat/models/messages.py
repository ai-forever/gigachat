from typing import Any, List, Optional

from gigachat.models.function_call import FunctionCall
from gigachat.models.messages_role import MessagesRole
from gigachat.pydantic_v1 import BaseModel, Field


class Messages(BaseModel):
    """Сообщение"""

    role: MessagesRole
    """Роль автора сообщения"""
    content: str = ""
    """Текст сообщения"""
    function_call: Optional[FunctionCall] = None
    """Вызов функции"""
    name: Optional[str] = None
    """Наименование функции. Заполняется, если role = "function" """
    attachments: Optional[List[str]] = None
    """Идентификаторы предзагруженных ранее файлов """
    data_for_context: Optional[List["Messages"]] = None
    """Данные для контекста"""
    id_: Optional[Any] = Field(alias="id")

    class Config:
        use_enum_values = True
