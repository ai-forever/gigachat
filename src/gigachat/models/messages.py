from gigachat.models.messages_role import MessagesRole
from gigachat.pydantic_v1 import BaseModel


class Messages(BaseModel):
    """Сообщение"""

    role: MessagesRole
    """Роль автора сообщения"""
    content: str
    """Текст сообщения"""

    class Config:
        use_enum_values = True
