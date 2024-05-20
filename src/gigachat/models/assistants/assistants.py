from typing import List

from gigachat.models.assistants.assistant import Assistant
from gigachat.pydantic_v1 import BaseModel


class Assistants(BaseModel):
    """Доступные ассистенты"""

    data: List[Assistant]
    """Массив объектов с данными доступных ассистентов"""
