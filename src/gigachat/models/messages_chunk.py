from gigachat.pydantic_v1 import BaseModel


class MessagesChunk(BaseModel):
    """Короткое сообщение"""

    content: str
    """Текст сообщения"""
