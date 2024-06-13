from enum import Enum


class MessagesRole(str, Enum):
    """Роль автора сообщения"""

    ASSISTANT = "assistant"
    SYSTEM = "system"
    USER = "user"
    FUNCTION = "function"
    SEARCH_RESULT = "search_result"
    FUNCTION_IN_PROGRESS = "function_in_progress"
