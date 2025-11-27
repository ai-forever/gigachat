from typing import List, Optional

from gigachat.models.utils import WithXHeaders
from gigachat.pydantic_v1 import BaseModel, Field


class EmbeddingsUsage(BaseModel):
    """Данные об использовании модели"""

    prompt_tokens: int
    """Количество токенов во входящем сообщении"""


class Embedding(BaseModel):
    """Ответ модели"""

    embedding: List[float]
    """Эмбеддинг"""
    usage: EmbeddingsUsage
    """Данные об использовании модели"""
    index: int
    """Индекс эмбеддинга в массиве"""
    object_: str = Field(alias="object")
    """Название объекта"""


class Embeddings(WithXHeaders):
    """Ответ модели"""

    data: List[Embedding]
    """Массив ответов эмбеддера"""
    model: Optional[str] = None
    """Название модели с помощью которой нужно вычислить эмбеддинги"""
    object_: str = Field(alias="object")
    """Название вызываемого метода"""
