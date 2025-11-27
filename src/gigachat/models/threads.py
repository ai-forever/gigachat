from enum import Enum
from typing import List, Literal, Optional, Union

from gigachat.models.chat import (
    ChatFunctionCall,
    ChoicesChunk,
    Function,
    FunctionCall,
    Messages,
    MessagesRole,
    Usage,
)
from gigachat.models.utils import WithXHeaders
from gigachat.pydantic_v1 import BaseModel, Field


class ThreadStatus(str, Enum):
    """Статус треда"""

    IN_PROGRESS = "in_progress"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class Thread(BaseModel):
    """Тред"""

    id_: str = Field(alias="id")
    """Идентификатор треда"""
    assistant_id: Optional[str]
    """Идентификатор ассистента. Передается при первом сообщении в сессию"""
    model: str
    """Алиас модели из Table.threads или из Table.assistants,
    если прикреплен assistant_id"""
    created_at: int
    """Дата создания сессии в Unix-time формате"""
    updated_at: int
    """Дата последней активности в сессии в Unix-time формате.
    Активностью считается добавление в сессию сообщения, run сессии"""
    run_lock: bool
    """Текущий статус запуска сессии"""
    status: ThreadStatus
    """Статус запуска"""


class Threads(WithXHeaders):
    """Треды"""

    threads: List[Thread]
    """Массив тредов клиента"""


class ThreadCompletion(WithXHeaders):
    """Ответ модели"""

    object_: str = Field(alias="object")
    """Название вызываемого метода"""
    model: str
    """Название модели, которая вернула ответ"""
    thread_id: str
    """Идентификатор треда"""
    message_id: str
    """Идентификатор сообщения ответа модели"""
    created: int
    """Дата и время создания ответа в формате Unix time"""
    usage: Usage
    """Данные об использовании модели"""
    message: Messages
    """Массив ответов модели"""
    finish_reason: str
    """Причина завершения гипотезы"""


class ThreadCompletionChunk(WithXHeaders):
    """Ответ модели"""

    object_: str = Field(alias="object")
    """Название вызываемого метода"""
    model: str
    """Название модели, которая вернула ответ"""
    thread_id: str
    """Идентификатор треда"""
    message_id: str
    """Идентификатор сообщения ответа модели"""
    created: int
    """Дата и время создания ответа в формате Unix time"""
    usage: Usage
    """Данные об использовании модели"""
    choices: List[ChoicesChunk]
    """Массив ответов модели в потоке"""


class ThreadMessageAttachment(BaseModel):
    """Файл"""

    file_id: str
    """Индентификатор предзагруженного ранее файла"""
    name: str
    """Наименование файла"""


class ThreadMessage(BaseModel):
    """Сообщение"""

    message_id: str
    """Идентификатор сообщения"""
    role: MessagesRole
    """Роль автора сообщения"""
    content: str = ""
    """Текст сообщения"""
    attachments: Optional[List[ThreadMessageAttachment]] = []
    """Идентификаторы предзагруженных ранее файлов"""
    created_at: int
    """Дата создания сообщения в Unix-time формате"""
    function_call: Optional[FunctionCall] = None
    """Вызов функции"""
    finish_reason: Optional[str] = None
    """Причина завершения гипотезы"""

    class Config:
        use_enum_values = True


class ThreadMessages(WithXHeaders):
    """Сообщения треда"""

    thread_id: str
    """Идентификатор треда"""
    messages: List[ThreadMessage]
    """Сообщения"""


class ThreadMessageResponse(BaseModel):
    created_at: int
    """Время создания сообщения в Unix-time формате"""
    message_id: str
    """Идентификатор созданного сообщения"""


class ThreadMessagesResponse(WithXHeaders):
    thread_id: str
    """Идентификатор треда"""
    messages: List[ThreadMessageResponse]
    """Созданные сообщения"""


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


class ThreadRunResponse(WithXHeaders):
    status: ThreadStatus
    """Статус запуска"""
    thread_id: str
    """Идентификатор запущенного треда"""
    created_at: int
    """Время запуска сессии в Unix-time формате"""


class ThreadRunResult(WithXHeaders):
    """Run треда"""

    status: ThreadStatus
    """Статус запуска"""
    thread_id: str
    """Идентификатор треда"""
    updated_at: int
    """Время обновления статуса run-a в Unix-time формате"""
    model: str
    """Модель"""
    messages: Optional[List[ThreadMessage]] = None
    """Сообщения"""
