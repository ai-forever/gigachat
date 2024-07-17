from gigachat.pydantic_v1 import BaseModel


class AssistantDelete(BaseModel):
    """Информация об удаленном ассистенте"""

    assistant_id: str
    """Идентификатор  ассистента"""
    deleted: bool
    """Признак удаления. Если true - ассистент удален"""
