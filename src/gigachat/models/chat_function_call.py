from gigachat.pydantic_v1 import BaseModel


class ChatFunctionCall(BaseModel):
    """Флаг, что мы ожидаем определенную функцию от llm"""

    name: str
    """Название функции"""
