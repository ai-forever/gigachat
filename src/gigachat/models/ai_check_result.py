from typing import List, Literal, Optional

from gigachat.pydantic_v1 import BaseModel


class AICheckResult(BaseModel):
    """Ответ модели"""

    category: Literal["ai", "human", "mixed"]
    """Результат проверки текста. Возможные значения: [ai, human, mixed]"""
    characters: int
    """Количество символов в переданном тексте"""
    tokens: int
    """Количество токенов в переданном тексте"""
    ai_intervals: Optional[List[List[int]]]
    """
    Части текста, сгенерированные моделью.
    Обозначаются индексами символов, с которых начинаются и заканчиваются сгенерированные фрагменты.
    """
