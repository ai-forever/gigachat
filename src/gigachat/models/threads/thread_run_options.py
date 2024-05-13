from typing import List, Literal, Optional, Union

from gigachat.models.chat_function_call import ChatFunctionCall
from gigachat.models.function import Function
from gigachat.pydantic_v1 import BaseModel


class ThreadRunOptions(BaseModel):
    """Параметры запроса"""

    temperature: Optional[float] = None
    """Температура выборки в диапазоне от ноля до двух"""
    top_p: Optional[float] = None
    """Альтернатива параметру температуры"""
    limit: Optional[int] = None
    """Максимальное количество сообщений исторического контекста, которые посылаются в модель в запросе
    Если параметр не передан, считаем что необходимо отправить весь контекст"""
    max_tokens: Optional[int] = None
    """Максимальное количество токенов, которые будут использованы для создания ответов"""
    repetition_penalty: Optional[float] = None
    """Количество повторений слов.
    Значение 1.0 - ничего не менять (нейтральное значение),
    от 0 до 1 - повторять уже сказанные слова,
    от 1 и далее стараться не использовать сказанные слова. Допустимое значение > 0"""
    profanity_check: Optional[bool] = None
    """Параметр цензуры"""
    flags: Optional[List[str]] = None
    """Флаги, включающие особенные фичи"""
    function_call: Optional[Union[Literal["auto", "none"], ChatFunctionCall]] = None
    """Правила вызова функций"""
    functions: Optional[List[Function]] = None
    """Набор функций, которые могут быть вызваны моделью"""
