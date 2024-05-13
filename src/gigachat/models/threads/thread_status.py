from enum import Enum


class ThreadStatus(str, Enum):
    """Статус треда"""

    IN_PROGRESS = "in_progress"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"
