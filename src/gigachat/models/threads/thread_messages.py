from typing import List

from gigachat.models.threads.thread_message import ThreadMessage
from gigachat.pydantic_v1 import BaseModel


class ThreadMessages(BaseModel):
    """Сообщения треда"""

    thread_id: str
    """Идентификатор треда"""
    messages: List[ThreadMessage]
    """Сообщения"""
