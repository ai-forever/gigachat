from gigachat.pydantic_v1 import BaseModel


class CreateAssistant(BaseModel):
    """Информация о созданном ассистенте"""

    assistant_id: str
    """Идентификатор созданного ассистента. UUIDv4"""
    created_at: int
    """Время создания ассистента в Unix-time формате"""
