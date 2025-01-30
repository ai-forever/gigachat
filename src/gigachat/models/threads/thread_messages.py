from typing import List

from gigachat.models.threads.thread_message import ThreadMessage
from gigachat.models.with_x_headers import WithXHeaders


class ThreadMessages(WithXHeaders):
    """Сообщения треда"""

    thread_id: str
    """Идентификатор треда"""
    messages: List[ThreadMessage]
    """Сообщения"""
