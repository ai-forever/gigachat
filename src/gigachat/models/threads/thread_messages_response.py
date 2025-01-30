from typing import List

from gigachat.models.threads.thread_message_response import ThreadMessageResponse
from gigachat.models.with_x_headers import WithXHeaders


class ThreadMessagesResponse(WithXHeaders):
    thread_id: str
    """Идентификатор треда"""
    messages: List[ThreadMessageResponse]
    """Созданные сообщения"""
