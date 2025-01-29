from typing import List

from gigachat.models.assistants.assistant import Assistant
from gigachat.models.with_x_headers import WithXHeaders


class Assistants(WithXHeaders):
    """Доступные ассистенты"""

    data: List[Assistant]
    """Массив объектов с данными доступных ассистентов"""
