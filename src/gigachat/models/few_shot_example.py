from typing import Any, Dict

from gigachat.pydantic_v1 import BaseModel


class FewShotExample(BaseModel):
    request: str
    """Запрос пользователя"""
    params: Dict[str, Any]
