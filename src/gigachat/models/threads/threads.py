from typing import List

from gigachat.models.threads.thread import Thread
from gigachat.models.with_x_headers import WithXHeaders


class Threads(WithXHeaders):
    """Треды"""

    threads: List[Thread]
    """Массив тредов клиента"""
