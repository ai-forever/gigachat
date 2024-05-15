from typing import Optional

from gigachat.models.threads.thread_status import ThreadStatus
from gigachat.pydantic_v1 import BaseModel, Field


class Thread(BaseModel):
    """Тред"""

    id_: str = Field(alias="id")
    """Идентификатор треда"""
    assistant_id: Optional[str]
    """Идентификатор ассистента. Передается при первом сообщении в сессию"""
    model: str
    """Алиас модели из Table.threads или из Table.assistants,
    если прикреплен assistant_id"""
    created_at: int
    """Дата создания сессии в Unix-time формате"""
    updated_at: int
    """Дата последней активности в сессии в Unix-time формате.
    Активностью считается добавление в сессию сообщения, run сессии"""
    run_lock: bool
    """Текущий статус запуска сессии"""
    status: ThreadStatus
    """Статус запуска"""
