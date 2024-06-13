from gigachat.models.threads.thread_status import ThreadStatus
from gigachat.pydantic_v1 import BaseModel


class ThreadRunResponse(BaseModel):
    status: ThreadStatus
    """Статус запуска"""
    thread_id: str
    """Идентификатор запущенного треда"""
    created_at: int
    """Время запуска сессии в Unix-time формате"""
