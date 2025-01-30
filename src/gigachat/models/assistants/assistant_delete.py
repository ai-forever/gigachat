from gigachat.models.with_x_headers import WithXHeaders


class AssistantDelete(WithXHeaders):
    """Информация об удаленном ассистенте"""

    assistant_id: str
    """Идентификатор  ассистента"""
    deleted: bool
    """Признак удаления. Если true - ассистент удален"""
