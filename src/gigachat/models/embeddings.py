from typing import List, Optional

from gigachat.models.embedding import Embedding
from gigachat.models.with_x_headers import WithXHeaders
from gigachat.pydantic_v1 import Field


class Embeddings(WithXHeaders):
    """Ответ модели"""

    data: List[Embedding]
    """Массив ответов эмбеддера"""
    model: Optional[str] = None
    """Название модели с помощью которой нужно вычислить эмбеддинги"""
    object_: str = Field(alias="object")
    """Название вызываемого метода"""
