from typing import Any, Dict, List, Optional

from gigachat.models.chat import Function
from gigachat.models.utils import WithXHeaders
from gigachat.pydantic_v1 import BaseModel


class AssistantAttachment(BaseModel):
    """Файл"""

    file_id: str
    """Идентификатор файла прикрепленного к ассистенту"""
    name: str
    """Имя файла прикрепленного к ассистенту"""


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


class Assistants(WithXHeaders):
    """Доступные ассистенты"""

    data: List[Assistant]
    """Массив объектов с данными доступных ассистентов"""


class AssistantDelete(WithXHeaders):
    """Информация об удаленном ассистенте"""

    assistant_id: str
    """Идентификатор  ассистента"""
    deleted: bool
    """Признак удаления. Если true - ассистент удален"""


class AssistantFileDelete(WithXHeaders):
    """Информация об удаленном файле"""

    file_id: str
    """Идентификатор прикрепленного к ассистенту файла"""
    deleted: bool
    """Признак удаления. Если true - файл удален из ассистента"""


class CreateAssistant(WithXHeaders):
    """Информация о созданном ассистенте"""

    assistant_id: str
    """Идентификатор созданного ассистента. UUIDv4"""
    created_at: int
    """Время создания ассистента в Unix-time формате"""
