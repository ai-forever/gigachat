from typing import List, Optional

from gigachat.models.threads.thread_message import ThreadMessage
from gigachat.models.threads.thread_status import ThreadStatus
from gigachat.pydantic_v1 import BaseModel


class ThreadRunResult(BaseModel):
    """Run треда"""

    status: ThreadStatus
    """Статус запуска"""
    thread_id: str
    """Идентификатор треда"""
    updated_at: int
    """Время обновления статуса run-a в Unix-time формате"""
    model: str
    """Модель"""
    messages: Optional[List[ThreadMessage]] = None
    """Сообщения"""
