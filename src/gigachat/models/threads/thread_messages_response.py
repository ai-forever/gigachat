from typing import List

from gigachat.models.threads.thread_message_response import ThreadMessageResponse
from gigachat.pydantic_v1 import BaseModel


class ThreadMessagesResponse(BaseModel):
    thread_id: str
    """Идентификатор треда"""
    messages: List[ThreadMessageResponse]
    """Созданные сообщения"""
