from gigachat.models.with_x_headers import WithXHeaders


class CreateAssistant(WithXHeaders):
    """Информация о созданном ассистенте"""

    assistant_id: str
    """Идентификатор созданного ассистента. UUIDv4"""
    created_at: int
    """Время создания ассистента в Unix-time формате"""
