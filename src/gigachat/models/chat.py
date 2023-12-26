from typing import List, Optional

from gigachat.models.messages import Messages
from gigachat.pydantic_v1 import BaseModel


class Chat(BaseModel):
    """Параметры запроса"""

    model: Optional[str] = None
    """Название модели, от которой нужно получить ответ"""
    messages: List[Messages]
    """Массив сообщений"""
    temperature: Optional[float] = None
    """Температура выборки в диапазоне от ноля до двух"""
    top_p: Optional[float] = None
    """Альтернатива параметру температуры"""
    n: Optional[int] = None
    """Количество вариантов ответов, которые нужно сгенерировать для каждого входного сообщения"""
    stream: Optional[bool] = None
    """Указывает, что сообщения надо передавать по частям в потоке"""
    max_tokens: Optional[int] = None
    """Максимальное количество токенов, которые будут использованы для создания ответов"""
    repetition_penalty: Optional[float] = None
    """Количество повторений слов"""
    update_interval: Optional[float] = None
    """Интервал в секундах между отправкой токенов в потоке"""
    profanity_check: Optional[bool] = None
    """Параметр цензуры"""
