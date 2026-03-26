# Руководство по миграции: с v1 на v2

Это руководство показывает, как перевести существующую интеграцию на GigaChat Python SDK с v1 chat API на v2 chat API.

В рамках этого репозитория под "v1" понимаются классические методы `chat()` / `stream()` / `achat()`, построенные вокруг `Chat`, `Messages` и `ChatCompletion`, которые работают с `/chat/completions`.

Под "v2" понимаются новые методы `chat_v2()` / `stream_v2()` / `achat_v2()`, построенные вокруг `ChatV2`, `ChatV2Message`, `ChatV2ContentPart` и `ChatCompletionV2`, которые работают с `/api/v2/chat/completions`.

## Для кого это руководство

Используйте его, если ваш код сейчас делает одно или несколько из следующих действий:

- Вызывает `client.chat(...)`, `client.stream(...)`, `client.achat(...)` или `client.astream(...)`
- Собирает запросы через `Chat` и `Messages`
- Читает ответы через `response.choices[0].message`
- Использует v1 `functions` / `function_call`
- Использует `chat_parse()` и хочет перейти на эквивалент для v2

Если вы используете только embeddings, files, models, retry или authentication, эти части SDK не требуют отдельной миграции для поддержки v2 chat API.

## Что меняется в v2

Главные изменения связаны со структурой данных:

- Вместо `Chat` используется `ChatV2`
- `content` сообщения больше не строка, а список структурированных частей контента
- Большинство параметров генерации переезжают в `model_options`
- Ответ больше не лежит в `choices[0].message`; теперь он приходит в верхнеуровневом `messages[]`
- Вызов функций переезжает в модель `tools` и `tool_config`
- Streaming использует именованные SSE-события вроде `response.message.delta` и `response.message.done`

При этом аутентификация, retry-логика и жизненный цикл клиента остаются прежними.

## Краткий чеклист миграции

1. Замените v1 chat-методы на v2 chat-методы.
2. Замените `Chat` на `ChatV2`.
3. Замените `Messages(content="...")` на структурированный `content=[{"text": "..."}]`.
4. Перенесите параметры генерации, такие как `temperature` и `max_tokens`, в `model_options`.
5. Обновите разбор ответа: вместо `choices[0].message` используйте `messages[]`.
6. Если вы используете структурированный JSON-ответ, замените `chat_parse()` на `chat_parse_v2()`.
7. Если вы используете function calling, замените `functions` / `function_call` на `tools` / `tool_config`.
8. Проверьте обработку `base_url`, если у вас кастомный deployment или gateway.

## Соответствие методов

| v1 | v2 |
|---|---|
| `client.chat(...)` | `client.chat_v2(...)` |
| `client.achat(...)` | `client.achat_v2(...)` |
| `client.stream(...)` | `client.stream_v2(...)` |
| `client.astream(...)` | `client.astream_v2(...)` |
| `client.chat_parse(...)` | `client.chat_parse_v2(...)` |
| `client.achat_parse(...)` | `client.achat_parse_v2(...)` |
| `Chat` | `ChatV2` |
| `Messages` | `ChatV2Message` |
| `ChatCompletion` | `ChatCompletionV2` |
| `ChatCompletionChunk` | `ChatCompletionV2Chunk` |

## Базовая миграция запроса

### v1

```python
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

chat = Chat(
    messages=[
        Messages(role=MessagesRole.SYSTEM, content="You are a concise assistant."),
        Messages(role=MessagesRole.USER, content="Write a short slogan for a coffee shop."),
    ],
    temperature=0.7,
    max_tokens=200,
)

with GigaChat(credentials="<your_authorization_key>") as client:
    response = client.chat(chat)
    print(response.choices[0].message.content)
```

### v2

```python
from gigachat import GigaChat
from gigachat.models import ChatV2

chat = ChatV2(
    messages=[
        {
            "role": "system",
            "content": [{"text": "You are a concise assistant."}],
        },
        {
            "role": "user",
            "content": [{"text": "Write a short slogan for a coffee shop."}],
        },
    ],
    model_options={
        "temperature": 0.7,
        "max_tokens": 200,
    },
)

with GigaChat(credentials="<your_authorization_key>") as client:
    response = client.chat_v2(chat)
    print("".join(part.text for part in response.messages[0].content if part.text))
```

### Что изменилось

- `Chat` заменен на `ChatV2`
- `Messages.content` поменялся с `str` на `list[ChatV2ContentPart]`
- `temperature` и `max_tokens` переехали в `model_options`
- Ответ переехал с `choices[0].message.content` на `messages[0].content[*].text`

## Соответствие полей запроса

Используйте эту таблицу, когда переносите типизированные payload-объекты или raw dict payload.

| v1 поле | v2 поле | Примечание |
|---|---|---|
| `messages[].role` | `messages[].role` | В v2 роль задается обычной строкой |
| `messages[].content: str` | `messages[].content: [{"text": "..."}]` | В v2 контент структурированный |
| `model` | `model` | Поле остается верхнеуровневым, если вы не используете `assistant_id` или существующий thread |
| `temperature` | `model_options.temperature` | Переехало в `model_options` |
| `top_p` | `model_options.top_p` | Переехало в `model_options` |
| `max_tokens` | `model_options.max_tokens` | Переехало в `model_options` |
| `repetition_penalty` | `model_options.repetition_penalty` | Переехало в `model_options` |
| `update_interval` | `model_options.update_interval` | Переехало в `model_options` |
| `unnormalized_history` | `model_options.unnormalized_history` | Переехало в `model_options` |
| `top_logprobs` | `model_options.top_logprobs` | Переехало в `model_options` |
| `reasoning_effort` | `model_options.reasoning.effort` | Изменилась структура |
| `response_format` | `model_options.response_format` | Переехало под `model_options` |
| `function_ranker` | `ranker_options` | Поле переименовано и расширено |
| `functions` | `tools=[{"functions": {"specifications": [...]}}]` | Изменился контейнер для функций |
| `function_call` | `tool_config` | Используются `mode`, `function_name` или `tool_name` |
| `storage.thread_id` | `storage.thread_id` | Поддерживается и в v2 |
| `storage.assistant_id` | `assistant_id` | Перемещено на верхний уровень |
| `storage.is_stateful` | `storage=True` или `storage={...}` | Прямого поля `is_stateful` в v2 больше нет |
| `messages[].attachments` | `messages[].content[].files` | Файлы теперь представляются как content parts |
| `profanity_check` | `disable_filter` | В v2 смотрите `disable_filter` и `filter_config` |

## Соответствие ответа

### Структура ответа v1

```python
message = response.choices[0].message
text = message.content
finish_reason = response.choices[0].finish_reason
prompt_tokens = response.usage.prompt_tokens
completion_tokens = response.usage.completion_tokens
```

### Структура ответа v2

```python
message = response.messages[0]
text_parts = [part.text for part in message.content if part.text is not None]
text = "".join(text_parts)
finish_reason = response.finish_reason
input_tokens = response.usage.input_tokens
output_tokens = response.usage.output_tokens
cached_tokens = (
    response.usage.input_tokens_details.cached_tokens
    if response.usage and response.usage.input_tokens_details
    else None
)
```

### Таблица соответствия полей ответа

| v1 | v2 |
|---|---|
| `response.choices[0].message` | `response.messages[0]` |
| `response.choices[0].message.content` | `response.messages[0].content[*].text` |
| `response.choices[0].message.function_call` | content part, где `part.function_call is not None` |
| `response.choices[0].finish_reason` | `response.finish_reason` |
| `response.usage.prompt_tokens` | `response.usage.input_tokens` |
| `response.usage.completion_tokens` | `response.usage.output_tokens` |
| `response.usage.precached_prompt_tokens` | `response.usage.input_tokens_details.cached_tokens` |

## Миграция streaming

### v1

```python
with GigaChat() as client:
    for chunk in client.stream("Write a haiku about Python"):
        print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### v2

```python
with GigaChat() as client:
    for chunk in client.stream_v2("Write a haiku about Python"):
        if chunk.event == "response.message.delta" and chunk.messages:
            for message in chunk.messages:
                for part in message.content or []:
                    if part.text:
                        print(part.text, end="", flush=True)
```

### Важные отличия streaming в v2

- В v1 дельты приходят через `choices[].delta`
- В v2 приходят именованные события
- В v2 могут приходить tool-related события, например `response.tool.in_progress` и `response.tool.completed`
- Финальная метаинформация по ответу обычно приходит в `response.message.done`

Если ваш старый stream-consumer предполагает, что каждый chunk содержит только текст, перед переходом на v2 его нужно обновить.

## Миграция структурированного вывода

И v1, и v2 поддерживают JSON Schema output, но место расположения параметров запроса меняется.

### v1 с `chat_parse()`

```python
from pydantic import BaseModel
from gigachat import GigaChat


class MathAnswer(BaseModel):
    steps: list[str]
    final_answer: str


with GigaChat() as client:
    completion, parsed = client.chat_parse(
        "Solve 8x + 7 = -23. Explain step by step.",
        response_model=MathAnswer,
        strict=True,
    )

print(parsed.final_answer)
```

### v2 с `chat_parse_v2()`

```python
from pydantic import BaseModel
from gigachat import GigaChat


class MathAnswer(BaseModel):
    steps: list[str]
    final_answer: str


with GigaChat() as client:
    completion, parsed = client.chat_parse_v2(
        "Solve 8x + 7 = -23. Explain step by step.",
        response_model=MathAnswer,
        strict=True,
    )

print(parsed.final_answer)
```

### Ручная миграция `response_format`

### v1

```python
chat = {
    "messages": [{"role": "user", "content": "Return JSON"}],
    "response_format": {
        "type": "json_schema",
        "schema": MyModel,
        "strict": True,
    },
}
```

### v2

```python
chat = {
    "messages": [{"role": "user", "content": [{"text": "Return JSON"}]}],
    "model_options": {
        "response_format": {
            "type": "json_schema",
            "schema": MyModel,
            "strict": True,
        }
    },
}
```

### Как теперь работает парсинг

`chat_parse_v2()` берет первое сообщение v2-ответа, в котором есть текстовый content part, и поднимает те же высокоуровневые исключения, что и v1:

- `ContentParseError`
- `ContentValidationError`
- `LengthFinishReasonError`
- `ContentFilterFinishReasonError`

## Миграция function calling и tools

В v1 используются `functions` и `function_call`.

В v2 используются `tools` и `tool_config`.

### v1

```python
from gigachat import GigaChat
from gigachat.models import Chat, Function, FunctionParameters, Messages, MessagesRole

weather_function = Function(
    name="weather-get",
    description="Get weather",
    parameters=FunctionParameters(
        type="object",
        properties={
            "location": {"type": "string", "description": "City name"},
        },
        required=["location"],
    ),
)

chat = Chat(
    messages=[Messages(role=MessagesRole.USER, content="What is the weather in Moscow?")],
    functions=[weather_function],
    function_call="auto",
)

with GigaChat() as client:
    response = client.chat(chat)
    message = response.choices[0].message

    if response.choices[0].finish_reason == "function_call":
        print(message.function_call.name)
        print(message.function_call.arguments)
```

### v2

```python
from gigachat import GigaChat
from gigachat.models import ChatV2, ChatV2Tool, Function, FunctionParameters

weather_function = Function(
    name="weather-get",
    description="Get weather",
    parameters=FunctionParameters(
        type="object",
        properties={
            "location": {"type": "string", "description": "City name"},
        },
        required=["location"],
    ),
)

chat = ChatV2(
    messages=[
        {
            "role": "user",
            "content": [{"text": "What is the weather in Moscow?"}],
        }
    ],
    tools=[ChatV2Tool.functions_tool([weather_function])],
    tool_config={"mode": "auto"},
)

with GigaChat() as client:
    response = client.chat_v2(chat)

    part_with_call = next(
        part
        for message in response.messages
        for part in message.content
        if part.function_call is not None
    )

print(part_with_call.function_call.name)
print(part_with_call.function_call.arguments)
```

### Как вернуть результат функции обратно в модель

В v1 результат функции обычно передается сообщением с `role="function"`.

В v2 результат передается как структурированный content part:

```python
follow_up = ChatV2(
    messages=[
        {
            "role": "tool",
            "tools_state_id": "tool-state-1",
            "content": [
                {
                    "function_result": {
                        "name": "weather-get",
                        "result": {
                            "temperature": 18,
                            "unit": "celsius",
                        },
                    }
                }
            ],
        }
    ]
)
```

Важно:

- Пользовательские функции теперь живут внутри `tools`
- Встроенные платформенные инструменты, такие как `web_search` и `image_generate`, используют тот же список `tools`
- Принудительный выбор инструмента во v2 настраивается через `tool_config={"mode": "forced", ...}`

## Stateful storage и assistants

В v2 меняется форма настроек для stateful conversation.

### v1

```python
chat = {
    "messages": [{"role": "user", "content": "Hello"}],
    "storage": {
        "is_stateful": True,
        "limit": 5,
        "assistant_id": "assistant-1",
        "metadata": {"topic": "demo"},
    },
}
```

### v2

```python
chat = {
    "messages": [{"role": "user", "content": [{"text": "Hello"}]}],
    "assistant_id": "assistant-1",
    "storage": {
        "limit": 5,
        "metadata": {"topic": "demo"},
    },
}
```

Важные правила для v2:

- `assistant_id` находится на верхнем уровне
- `assistant_id` и `model` взаимоисключающие
- `assistant_id` и `storage.thread_id` тоже взаимоисключающие
- Чтобы включить stateful storage без дополнительных параметров, можно передать `storage=True`
- Если используется `assistant_id` или уже существующий `storage.thread_id`, SDK не будет автоматически подставлять default model

## Миграция `base_url` и endpoint

Для v1 SDK использует классический endpoint `/chat/completions`.

Для v2 SDK вычисляет URL из `base_url`:

- Если `base_url` заканчивается на `/v2`, запросы пойдут на `/v2/chat/completions`
- Если `base_url` заканчивается на `/v1`, SDK автоматически заменит его на `/v2/chat/completions`
- Если `base_url` уже указывает на `/v2/chat/completions`, он будет использован напрямую
- Если SDK не может вывести v2 URL автоматически, будет выброшен `ValueError`

Если у вас кастомный deployment или gateway, задайте `chat_v2_url_cvar` явно:

```python
from gigachat import GigaChat, chat_v2_url_cvar

token = chat_v2_url_cvar.set("https://example.com/custom/api/v2/chat/completions")
try:
    with GigaChat(base_url="https://example.com/api/v1") as client:
        response = client.chat_v2("Hello")
finally:
    chat_v2_url_cvar.reset(token)
```

## Частые ошибки

### 1. Относиться к v2 `content` как к строке

Это самая частая ошибка при миграции.

Неправильно:

```python
text = response.messages[0].content
```

Правильно:

```python
text = "".join(part.text for part in response.messages[0].content if part.text)
```

### 2. Оставить параметры генерации на верхнем уровне

Неправильно:

```python
chat = {
    "messages": [...],
    "temperature": 0.2,
}
```

Правильно:

```python
chat = {
    "messages": [...],
    "model_options": {"temperature": 0.2},
}
```

### 3. Искать `finish_reason` внутри `choices[0]`

Во v2 `finish_reason` находится на верхнем уровне ответа.

### 4. Предполагать, что stream содержит только текст

Во v2 stream может содержать tool events и нетекстовые content parts.

### 5. Оставить старые предположения о function calling

`functions` и `function_call` больше не являются верхнеуровневыми полями v2. Их нужно переносить в `tools` и `tool_config`.

### 6. Использовать кастомный `base_url`, который не заканчивается на `/v1` или `/v2`

Для v1 это может работать, а вот автоматический вывод v2 URL может сломаться. В таком случае задайте `chat_v2_url_cvar` явно.

## Минимальный пример до и после

Если старый код выглядел так:

```python
from gigachat import GigaChat

with GigaChat(credentials="<your_authorization_key>") as client:
    response = client.chat("Hello!")
    print(response.choices[0].message.content)
```

То минимальная версия для v2 выглядит так:

```python
from gigachat import GigaChat

with GigaChat(credentials="<your_authorization_key>") as client:
    response = client.chat_v2("Hello!")
    print("".join(part.text for part in response.messages[0].content if part.text))
```

## Рекомендуемая стратегия миграции

Для production-кода безопаснее всего идти в таком порядке:

1. Перевести сборку запросов с `Chat` на `ChatV2`
2. Обновить helpers для разбора ответа
3. Обновить stream-consumers
4. Перевести JSON Schema helpers на `chat_parse_v2()`
5. Перевести function calling на `tools`
6. Протестировать stateful thread и assistant flows
7. Проверить кастомные deployment-сценарии с `base_url`

## Итог

Миграция на v2 в первую очередь сводится к миграции формы данных:

- текстовые сообщения становятся структурированными content parts
- параметры модели переезжают в `model_options`
- ответы переезжают с `choices[].message` на `messages[]`
- tools заменяют старую обвязку function calling

После этого остальная работа с SDK остается знакомой: тот же жизненный цикл клиента, та же схема аутентификации, те же sync/async-паттерны и тот же набор высокоуровневых parse-exceptions.
