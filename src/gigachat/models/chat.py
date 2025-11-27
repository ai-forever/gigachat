from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from gigachat.models.utils import WithXHeaders
from gigachat.pydantic_v1 import BaseModel, Field, root_validator


class MessagesRole(str, Enum):
    """Роль автора сообщения"""

    ASSISTANT = "assistant"
    SYSTEM = "system"
    USER = "user"
    FUNCTION = "function"
    SEARCH_RESULT = "search_result"
    FUNCTION_IN_PROGRESS = "function_in_progress"


class FunctionCall(BaseModel):
    """Вызов функции"""

    name: str
    """Название функции"""
    arguments: Optional[Dict[Any, Any]] = None
    """Описание функции"""


class FewShotExample(BaseModel):
    request: str
    """Запрос пользователя"""
    params: Dict[str, Any]


class Storage(BaseModel):
    """Данные для хранения контекста на стороне GigaChat"""

    is_stateful: bool
    """
    Режим сохранения сообщений контекста.
    При работе с данным режимом не требуется передавать сообщения контекста каждый раз.
    Достаточно передать только новое сообщение
    """
    limit: Optional[int] = None
    """
    Максимальное количество сообщений исторического контекста, которые посылаются в модель в запросе.
    Если пользователь передает limit на генерацию ответа от модели и у него есть system в истории или
    инструкция у ассистента, то кол-во сообщений отправленных в модель = limit + 1,
    т.е. к лимиту добавляется систем промпт.
    Если параметр не передан, считаем что необходимо отправить весь контекст.
    """
    assistant_id: Optional[str] = None
    """
    Идентификатор ассистента при создании треда (только в первом сообщении).
    При передаче идентификатора  нельзя передавать поле model.
    При передаче id треда этот идентификатор не передается
    """
    thread_id: Optional[str] = None
    """Идентификатор треда. Не заполняется для первого сообщения"""
    metadata: Optional[Dict[Any, Any]] = None


class Usage(BaseModel):
    """Данные об использовании модели"""

    prompt_tokens: int
    """Количество токенов во входящем сообщении"""
    completion_tokens: int
    """Количество токенов, сгенерированных моделью"""
    total_tokens: int
    """Общее количество токенов"""
    precached_prompt_tokens: Optional[int]
    """Количество токенов попавших в кэш"""


class FunctionParametersProperty(BaseModel):
    """Функция, которая может быть вызвана моделью"""

    type_: str = Field(default="object", alias="type")
    """Тип аргумента функции"""
    description: str = ""
    """Описание аргумента"""
    items: Optional[Dict[str, Any]] = None
    """Возможные значения аргумента"""
    enum: Optional[List[str]] = None
    """Возможные значения enum"""
    properties: Optional[Dict[Any, "FunctionParametersProperty"]] = None


class FunctionParameters(BaseModel):
    """Функция, которая может быть вызвана моделью"""

    type_: str = Field(default="object", alias="type")
    """Тип параметров функции"""
    properties: Optional[Dict[Any, FunctionParametersProperty]] = None
    """Описание функции"""
    required: Optional[List[str]] = None
    """Список обязательных параметров"""


class Function(BaseModel):
    """Функция, которая может быть вызвана моделью"""

    name: str
    """Название функции"""
    description: Optional[str] = None
    """Описание функции"""
    parameters: Optional[FunctionParameters] = None
    """Список параметров функции"""
    few_shot_examples: Optional[List[FewShotExample]] = None
    return_parameters: Optional[Dict[Any, Any]] = None
    """Список возвращаемых параметров функции"""

    @root_validator(pre=True)
    def _fix_title_and_parameters(cls, values):
        """Pydantic adapter (title -> name), (parameters -> properties)"""
        if isinstance(values, dict):
            values = dict(values)

            if values.get("name") in (None, "") and values.get("title"):
                values["name"] = values.pop("title", None)

            if values.get("parameters") in (None, "", {}) and "properties" in values:
                values["parameters"] = {
                    "properties": values.pop("properties", {}),
                }

        return values


class ChatFunctionCall(BaseModel):
    """Флаг, что мы ожидаем определенную функцию от llm"""

    name: str
    """Название функции"""
    partial_arguments: Optional[Dict[str, Any]] = None
    """Часть аргументов функции"""


class Messages(BaseModel):
    """Сообщение"""

    role: MessagesRole
    """Роль автора сообщения"""
    content: str = ""
    """Текст сообщения"""
    function_call: Optional[FunctionCall] = None
    """Вызов функции"""
    name: Optional[str] = None
    """Наименование функции. Заполняется, если role = "function" """
    attachments: Optional[List[str]] = None
    """Идентификаторы предзагруженных ранее файлов """
    data_for_context: Optional[List["Messages"]] = None
    """DEPRECATED: Данные для контекста"""
    functions_state_id: Optional[str] = None
    """ID сообщений функций генерирующий изображения/видео"""
    reasoning_content: Optional[str] = None
    """Рассуждения модели"""
    id_: Optional[Any] = Field(alias="id", default=None)

    class Config:
        use_enum_values = True


class MessagesChunk(BaseModel):
    """Короткое сообщение"""

    role: Optional[MessagesRole] = None
    """Роль автора сообщения"""
    content: Optional[str] = None
    """Текст сообщения"""
    reasoning_content: Optional[str] = None
    """Reasoning токены"""
    function_call: Optional[FunctionCall] = None
    """Вызов функции"""
    functions_state_id: Optional[str] = None
    """Идентификатор вызова функции"""


class Choices(BaseModel):
    """Ответ модели"""

    message: Messages
    """Сгенерированное сообщение"""
    index: int
    """Индекс сообщения в массиве начиная с нуля"""
    finish_reason: Optional[str] = None
    """Причина завершения гипотезы"""


class ChoicesChunk(BaseModel):
    """Ответ модели в потоке"""

    delta: MessagesChunk
    """Короткое сообщение"""
    index: int
    """Индекс сообщения в массиве начиная с нуля"""
    finish_reason: Optional[str] = None
    """Причина завершения гипотезы"""


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
    function_call: Optional[Union[Literal["auto", "none"], ChatFunctionCall]] = None
    """Правила вызова функций"""
    functions: Optional[List[Function]] = None
    """Набор функций, которые могут быть вызваны моделью"""
    flags: Optional[List[str]] = None
    """Флаги, включающие особенные фичи"""
    storage: Optional[Storage] = None
    """Данные для хранения контекста на стороне GigaChat"""
    additional_fields: Optional[dict] = None
    """Дополнительные поля, которые прокидываются в API /chat/completions"""
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None
    """Глубина рассуждений"""


class ChatCompletion(WithXHeaders):
    """Ответ модели"""

    choices: List[Choices]
    """Массив ответов модели"""
    created: int
    """Дата и время создания ответа в формате Unix time"""
    model: str
    """Название модели, которая вернула ответ"""
    thread_id: Optional[str] = None
    """Идентификатор треда"""
    message_id: Optional[str] = None
    """Идентификатор сообщения. Для storage_mode - true"""
    usage: Usage
    """Данные об использовании модели"""
    object_: str = Field(alias="object")
    """Название вызываемого метода"""


class ChatCompletionChunk(WithXHeaders):
    """Ответ модели в потоке"""

    choices: List[ChoicesChunk]
    """Массив ответов модели в потоке"""
    created: int
    """Дата и время создания ответа в формате Unix time"""
    model: str
    """Название модели, которая вернула ответ"""
    object_: str = Field(alias="object")
    """Наименование вызываемого метода"""
    usage: Optional[Usage] = None
    """Данные о потребленных токенах"""
