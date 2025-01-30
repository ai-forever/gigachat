from gigachat.models.threads.thread_status import ThreadStatus
from gigachat.models.with_x_headers import WithXHeaders


class ThreadRunResponse(WithXHeaders):
    status: ThreadStatus
    """Статус запуска"""
    thread_id: str
    """Идентификатор запущенного треда"""
    created_at: int
    """Время запуска сессии в Unix-time формате"""
