from gigachat.pydantic_v1 import BaseModel


class ThreadMessageResponse(BaseModel):
    created_at: int
    """Время создания сообщения в Unix-time формате"""
    message_id: str
    """Идентификатор созданного сообщения"""
