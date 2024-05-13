from typing import List

from gigachat.models.threads.thread import Thread
from gigachat.pydantic_v1 import BaseModel


class Threads(BaseModel):
    """Треды"""

    threads: List[Thread]
    """Массив тредов клиента"""
