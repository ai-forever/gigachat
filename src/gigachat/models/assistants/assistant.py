from typing import Any, Dict, List, Optional

from gigachat.models import Function
from gigachat.models.assistants.assistant_attachment import AssistantAttachment
from gigachat.pydantic_v1 import BaseModel


class Assistant(BaseModel):
    """Ассистент"""

    model: str
    """Идентификатор модели, которую необходимо использовать."""
    assistant_id: str
    """Идентификатор созданного ассистента. UUIDv4"""
    name: Optional[str]
    """Имя ассистента, которое было передано в запросе"""
    description: Optional[str]
    """Описание ассистента, которое было передано в запросе"""
    instructions: Optional[str]
    """Инструкция для ассистента, которое было передано в запросе"""
    created_at: int
    """Время создания ассистента в Unix-time формате"""
    updated_at: int
    """Время изменения ассистента в Unix-time формате"""
    files: Optional[List[AssistantAttachment]]
    """Файлы прикрепленные к ассистенту """
    metadata: Optional[Dict[str, Any]]
    """Дополнительная информация"""
    threads_count: Optional[int]
    """Количество тредов клиента взаимодействующих с этим ассистентом"""
    functions: Optional[List[Function]]
    """Описания функций, с которыми может работать ассистент"""
