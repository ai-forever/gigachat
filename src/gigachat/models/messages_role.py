from enum import Enum


class MessagesRole(str, Enum):
    """Роль автора сообщения"""

    ASSISTANT = "assistant"
    SYSTEM = "system"
    USER = "user"
