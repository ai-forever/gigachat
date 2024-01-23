from typing import Any, Dict, Optional

from gigachat.pydantic_v1 import BaseModel


class FunctionCall(BaseModel):
    """Вызов функции"""

    name: str
    """Название функции"""
    arguments: Optional[Dict[Any, Any]] = None
    """Описание функции"""
