# Руководство по миграции на v2

Этот документ описывает переход с legacy-контракта чата на основной surface `chat/completions`, который появился в v2.

В кодовой базе `v2` представлен как primary API. Предыдущий контракт по-прежнему доступен через явные пространства имен `.legacy`.

## Кратко

1. Замените `client.chat(...)` на `client.chat.create(...)` или `client.chat.legacy.create(...)`.
2. Замените `client.stream(...)` на `client.chat.stream(...)` или `client.chat.legacy.stream(...)`.
3. Замените `client.chat_parse(...)` на `client.chat.parse(...)` или `client.chat.legacy.parse(...)`.
4. Замените legacy-модели вроде `Chat` и `Messages` на primary-модели `ChatCompletionRequest` и `ChatMessage`.
5. Перенесите чтение ответа с `response.choices[0].message.content` на primary `messages[*].content[*].text`.

## Зачем вообще появился v2

v2 это не просто переименование старого endpoint. Это отдельный контракт, рассчитанный на более широкий chat surface:

- составной контент сообщений, включая multipart content и ссылки на файлы
- stateful-сценарии через assistants и threads
- единая модель для tool execution, function calling и structured output
- более богатые метаданные ответа, включая `thread_id`, `tool_execution` и новую схему token usage

В v1 почти весь полезный ответ жил внутри `choices[0].message`. Такой формат слишком узок для новых сценариев, где API может возвращать несколько сообщений, состояние tools, execution metadata и multipart content. В v2 эти сущности стали частью основного контракта, а не побочными расширениями.

## Что именно меняется

Миграция состоит из трех разных слоев. Если разделять их явно, переход делать проще:

1. Изменение способа вызова
   Убираем deprecated root shim-ы и переходим на явные resource methods.
2. Изменение request-моделей
   Переходим с legacy-моделей на primary-модели.
3. Изменение обработки response
   Обновляем код, который читает текст ответа, usage, tool calls и streaming chunks.

Если у вас код просто отправляет строку и печатает ответ, миграция небольшая. Если вы сами строите payload, используете structured output или function calling, это уже полноценная смена контракта, а не косметический rename.

## Изменения публичного API

| Legacy-вызов | Primary-вызов v2 | Если нужен старый wire-format |
| --- | --- | --- |
| `client.chat(payload)` | `client.chat.create(payload)` | `client.chat.legacy.create(payload)` |
| `client.stream(payload)` | `client.chat.stream(payload)` | `client.chat.legacy.stream(payload)` |
| `client.chat_parse(payload, response_format=...)` | `client.chat.parse(payload, response_format=...)` | `client.chat.legacy.parse(payload, response_format=...)` |
| `await client.achat(payload)` | `await client.achat.create(payload)` | `await client.achat.legacy.create(payload)` |
| `client.astream(payload)` | `client.achat.stream(payload)` | `client.achat.legacy.stream(payload)` |
| `await client.achat_parse(payload, response_format=...)` | `await client.achat.parse(payload, response_format=...)` | `await client.achat.legacy.parse(payload, response_format=...)` |

`client.chat(...)`, `client.stream(...)`, `client.chat_parse(...)`, `client.achat(...)`, `client.astream(...)` и `client.achat_parse(...)` пока работают, но это deprecated shim-ы. Они вызывают `DeprecationWarning`.

Non-chat endpoint-ы тоже используют явные resource namespaces. Старые root-методы пока работают как deprecated
compatibility shim-ы и вызывают `DeprecationWarning`; в новом коде используйте resource paths ниже.

| Deprecated root-вызов | Resource-вызов |
| --- | --- |
| `client.get_models()` | `client.models.list()` |
| `client.get_model(model)` | `client.models.retrieve(model)` |
| `await client.aget_models()` | `await client.a_models.list()` |
| `await client.aget_model(model)` | `await client.a_models.retrieve(model)` |
| `client.embeddings(texts, model=...)` | `client.embeddings.create(texts, model=...)` |
| `await client.aembeddings(texts, model=...)` | `await client.a_embeddings.create(texts, model=...)` |
| `client.upload_file(file, purpose=...)` | `client.files.upload(file, purpose=...)` |
| `client.get_file(file)` | `client.files.retrieve(file)` |
| `client.get_files()` | `client.files.list()` |
| `client.delete_file(file)` | `client.files.delete(file)` |
| `client.get_file_content(file_id)` | `client.files.retrieve_content(file_id)` |
| `client.get_image(file_id)` | `client.files.retrieve_content(file_id)` |
| `client.create_batch(file, method)` | `client.batches.create(file, method)` |
| `client.get_batches()` | `client.batches.list()` |
| `client.get_batches(batch_id="...")` | `client.batches.retrieve("...")` |
| `await client.aupload_file(file, purpose=...)` | `await client.a_files.upload(file, purpose=...)` |
| `await client.aget_file(file)` | `await client.a_files.retrieve(file)` |
| `await client.aget_files()` | `await client.a_files.list()` |
| `await client.adelete_file(file)` | `await client.a_files.delete(file)` |
| `await client.aget_file_content(file_id)` | `await client.a_files.retrieve_content(file_id)` |
| `await client.aget_image(file_id)` | `await client.a_files.retrieve_content(file_id)` |
| `await client.acreate_batch(file, method)` | `await client.a_batches.create(file, method)` |
| `await client.aget_batches()` | `await client.a_batches.list()` |
| `await client.aget_batches(batch_id="...")` | `await client.a_batches.retrieve("...")` |
| `client.tokens_count(input_, model=...)` | `client.tokens.count(input_, model=...)` |
| `await client.atokens_count(input_, model=...)` | `await client.a_tokens.count(input_, model=...)` |
| `client.get_balance()` | `client.balance.get()` |
| `await client.aget_balance()` | `await client.a_balance.get()` |
| `client.openapi_function_convert(openapi_function)` | `client.functions.convert_openapi(openapi_function)` |
| `await client.aopenapi_function_convert(openapi_function)` | `await client.a_functions.convert_openapi(openapi_function)` |
| `client.validate_function(function)` | `client.functions.validate(function)` |
| `await client.avalidate_function(function)` | `await client.a_functions.validate(function)` |
| `client.check_ai(text, model)` | `client.ai_check.check(text, model)` |
| `await client.acheck_ai(text, model)` | `await client.a_ai_check.check(text, model)` |

`client.files.retrieve_image(file_id)` и `await client.a_files.retrieve_image(file_id)` остаются deprecated
image-only compatibility alias-ами. В новом коде используйте `retrieve_content(...)` для любого содержимого файла.

Primary chat completions используют v2 route. Если клиентский `base_url` все еще заканчивается на `/v1`, вызовы `client.chat.create(...)`, `client.chat.stream(...)`, `client.achat.create(...)` и `client.achat.stream(...)` автоматически уходят на соответствующий `/v2/chat/completions`. Явные override-ы `chat_completions_url` по-прежнему учитываются, включая versioned paths вроде `/v2/chat/completions`.

Почему это поменялось:

- `client.chat` и `client.achat` теперь являются resource namespace, а не только callable shim-ами
- такой layout делает SDK консистентным и оставляет место для нескольких операций: `create`, `stream`, `parse`
- ветка `.legacy` сохраняет старый контракт доступным, но не делает его дефолтным

## Рекомендуемая стратегия миграции

Для production-кода безопаснее идти по шагам:

1. Уберите вызовы deprecated root shim-ов.
   Сначала перейдите на `client.chat.create()` / `client.chat.stream()` / `client.chat.parse()`.
2. Если payload пока сложно переносить, временно перейдите на `.legacy`.
   Это снимет warnings без немедленного полного переписывания контракта.
3. Перенесите request-модели.
   Замените `Chat` и `Messages` на `ChatCompletionRequest` и `ChatMessage`.
4. Перепишите чтение response.
   Обновите весь код, который читает `choices`, `message.content`, `created` или legacy `usage`.
5. Перенесите structured output и tool-calling код.
   Именно здесь primary-контракт дает наибольшую пользу.

Этот порядок важен: замена deprecated shim-ов обычно механическая, а миграция response/payload чаще всего затрагивает прикладную логику.

## Миграция request-моделей

Primary-контракт запроса не является расширением legacy-контракта. Если у вас не тривиальный payload, его лучше явно перенести на `ChatCompletionRequest`.

| Legacy | Primary v2 |
| --- | --- |
| `Chat` | `ChatCompletionRequest` |
| `Messages` | `ChatMessage` |
| `MessagesRole.USER` | `"user"` |
| `response_format` в legacy `Chat` | `model_options.response_format` в `ChatCompletionRequest` |
| строковый `message.content` | `content`, который нормализуется в список частей |

Почему это поменялось:

- v1 моделировал сообщение в первую очередь как одну строку
- v2 моделирует сообщение как набор content parts, чтобы в одном объекте переносить текст, файлы, tool results и inline metadata
- новые возможности больше не прячутся в неудобных расширениях, а вынесены в явные поля вроде `assistant_id`, `tool_config` и `storage`

В primary-запросе появились поля, которых раньше не было:

- `assistant_id`
- `tools_state_id`
- multipart `messages[].content`
- `model_options`
- `model_options.reasoning`
- `model_options.response_format`
- `filter_config`
- `storage.thread_id`
- `ranker_options`
- `tool_config`
- `tools`
- `user_info`
- `stream`
- `disable_filter`
- `flags`

### Было

```python
from gigachat.models import Chat, Messages, MessagesRole

payload = Chat(
    messages=[
        Messages(
            role=MessagesRole.USER,
            content="Hello!",
        )
    ]
)

response = client.chat.legacy.create(payload)
```

### Стало

```python
from gigachat.models import ChatCompletionRequest, ChatMessage

payload = ChatCompletionRequest(
    messages=[
        ChatMessage(
            role="user",
            content="Hello!",
        )
    ]
)

response = client.chat.create(payload)
```

Важно:

- По-прежнему можно передать просто строку: `client.chat.create("Hello!")`.
- В primary API поле `content` принимает строку, один объект или список; SDK нормализует это в список частей.
- При вызове через клиент `model` по умолчанию заполняется как `GigaChat-2`, кроме сценариев с `assistant_id` или существующим `storage.thread_id`.
- SDK принимает top-level `response_format` и `reasoning` как удобный ввод в `ChatCompletionRequest`, но при сериализации переносит их в `model_options`.
- `tools` принимает полные tool objects и поддержанные shorthand-строки: `"code_interpreter"`, `"image_generate"`, `"web_search"`, `"url_content_extraction"`, `"model_3d_generate"` и `"functions"`.

### Как теперь думать про `content`

В v1 типичная ментальная модель была такой:

- одно сообщение
- одна строка

В v2 модель другая:

- одно сообщение
- ноль или больше content parts

Именно поэтому `ChatMessage(content="Hello!")` по-прежнему работает, но внутри SDK нормализуется примерно к такому виду:

```python
[
    {"text": "Hello!"}
]
```

Это важно, потому что когда позже вы добавите файлы, inline metadata или tool results, для них уже не понадобится отдельная боковая структура.

### Типичный rewrite запроса с v1 на v2

Если раньше вы вручную собирали request-объект, то обычно миграция выглядит так:

1. Заменить `Chat(...)` на `ChatCompletionRequest(...)`.
2. Заменить каждый `Messages(...)` на `ChatMessage(...)`.
3. Перевести enum-роли в строковые роли.
4. Переписать логику, которая считает `content` обычной строкой.
5. Не копировать legacy-поля механически, а переосмыслить их в терминах primary-контракта.

Последний пункт принципиален: v2 достаточно похож на v1, чтобы возникало желание переносить поля один в один, но для нетривиальных payload это часто приводит к полумере вместо реальной миграции.

## Миграция response-моделей

Форма primary-ответа существенно отличается от legacy.

| Legacy create response | Primary response v2 |
| --- | --- |
| `response.choices[0].message.content` | `"".join(part.text or "" for part in assistant_message.content or [])` |
| `response.usage.prompt_tokens` | `response.usage.input_tokens` |
| `response.usage.completion_tokens` | `response.usage.output_tokens` |
| `response.created` | `response.created_at` |
| streaming `chunk.choices` | streaming `chunk.messages` |

Почему это поменялось:

- v1 предполагал, что основной ответ всегда живет в `choices[0].message`
- v2 допускает message-oriented ответы и метаданные tools на верхнем уровне, поэтому основной контейнер теперь `messages`
- usage был переименован так, чтобы точнее отражать семантику запроса и ответа: `input_tokens` и `output_tokens`

### Было

```python
text = response.choices[0].message.content
```

### Стало

```python
message = next(message for message in response.messages if message.role == "assistant")
text = "".join(part.text or "" for part in message.content or [])
```

В primary-ответах также могут приходить `thread_id`, `tool_execution`, `logprobs` и opaque-элементы `additional_data`.

### Почему чаще всего ломается именно чтение ответа

Самая частая ошибка при миграции связана не с request payload, а с downstream-кодом, который предполагает, что:

- `response.choices` всегда существует
- `message.content` всегда строка
- есть поля `usage.prompt_tokens` и `usage.completion_tokens`
- streaming chunks выглядят как legacy chunks

Ищите по коду такие паттерны:

- `choices[0]`
- `.message.content`
- `prompt_tokens`
- `completion_tokens`
- `created`

Обычно именно эти места требуют реального переписывания логики, а не простого rename.

### Рекомендуемый способ доставать текст

Если приложению нужен только текст assistant-сообщения, лучше сделать явный helper в своем коде, а не дублировать `join(...)` в десятках мест:

```python
def extract_text(message):
    return "".join(part.text or "" for part in message.content or [])
```

Это даст одну точку изменений, если позже вы начнете обрабатывать файлы или нетекстовые части сообщения.

## Миграция streaming

Для streaming обычно недостаточно просто переименовать метод.

### Было

```python
for chunk in client.stream("Write a poem"):
    if chunk.choices:
        print(chunk.choices[0].delta.content or "", end="")
```

### Стало

```python
for chunk in client.chat.stream("Write a poem"):
    if chunk.messages and chunk.messages[0].content:
        print("".join(part.text or "" for part in chunk.messages[0].content), end="")
```

Почему это поменялось:

- primary streaming работает через message-based chunks
- primary streaming парсится как named SSE events, поэтому `chunk.event` может быть `response.message.delta`, `response.tool.completed`, `response.message.done` и другими event name
- финальные или tool-related chunks могут содержать только `finish_reason`, `usage`, `tools_state_id`, `tool_execution` или metadata без текста
- рядом с текстом могут приходить tool execution и другая метаинформация

Legacy streaming по-прежнему использует старый parser `data:`-строк и legacy chunk model. Primary streaming использует event-aware parser и не требует маркера `[DONE]`. Если ваш streaming consumer склеивает частичные токены, проверьте эту логику отдельно. Предположения legacy `delta`-стиля не всегда напрямую переносятся на primary `messages`.

## Миграция structured output

Если раньше вы пользовались legacy-методами parse, то при переходе на v2 имеет смысл перейти и на primary parse.

### Было

```python
completion, parsed = client.chat_parse(
    "Solve 8x + 7 = -23",
    response_format=MathAnswer,
)
```

### Стало

```python
completion, parsed = client.chat.parse(
    "Solve 8x + 7 = -23",
    response_format=MathAnswer,
)
```

Важно:

- `client.chat.parse()` и `client.achat.parse()` отправляют primary-запрос с `response_format={"type": "json_schema", ...}`.
- На wire-уровне эта схема отправляется как `model_options.response_format`.
- Если вы хотите остаться на старом контракте, используйте `client.chat.legacy.parse()` и `client.achat.legacy.parse()`.
- Передача Pydantic-модели в `response_format` у legacy `create()` не является заменой миграции; в этом сценарии нужно использовать `parse()`.

Почему в v2 это лучше:

- structured output стал частью primary-контракта, а не надстройкой вокруг legacy-response
- SDK парсит assistant text уже из primary `messages`
- схема запроса представлена явно как `ChatResponseFormat(type="json_schema", ...)`

Если ваш код уже серьезно зависит от schema-validated output, перенос parse-хелперов лучше делать раньше, а не откладывать на конец.

## Function calling и advanced-возможности

Если ваша интеграция использует или планирует использовать:

- function calling
- built-in tools вроде web search
- stateful conversation через assistants
- thread storage
- богатые response metadata

то именно v2 является правильной целевой моделью.

Причина структурная: эти возможности естественно ложатся в primary request/response model, а в v1 они либо уже узкие, либо описаны через legacy-специфику.

Например, в v2 для этого есть явные request fields:

- `tools`
- `tool_config`
- `assistant_id`
- `storage`
- `ranker_options`
- `user_info`

Если в roadmap вашего приложения есть такие сценарии, то миграция только вызовов методов без перехода на primary payload обычно является временной полумерой.

## Миграция импортов моделей

На переходный период старые импорты продолжают указывать на legacy alias-ы.

| Старый импорт | Что это означает сейчас | Чем заменить |
| --- | --- | --- |
| `from gigachat.models import Chat` | Legacy request alias | `from gigachat.models import ChatCompletionRequest` |
| `from gigachat.models import Messages` | Legacy message alias | `from gigachat.models import ChatMessage` |
| `from gigachat.models import ChatCompletion` | Legacy response alias | `from gigachat.models import ChatCompletionResponse` |
| `from gigachat.models import Usage` | Legacy usage alias | `from gigachat.models import ChatUsage` |
| `from gigachat.models import Storage` | Legacy storage alias | `from gigachat.models import ChatStorage` |
| `from gigachat.models import ChatCompletionChunk` | Legacy streaming chunk alias | `from gigachat.models.chat_completions import ChatCompletionChunk` |
| `from gigachat.models import ChatFunctionCall` | Legacy function-call alias | `from gigachat.models.chat_completions import ChatFunctionCall` |

Для primary-типов с конфликтующими именами лучше импортировать напрямую из `gigachat.models.chat_completions`.

Почему прямые импорты важны:

- часть top-level имен намеренно сохранена как legacy alias ради backwards compatibility
- прямой импорт из `gigachat.models.chat_completions` убирает двусмысленность
- особенно это важно для имен с конфликтом, например `ChatCompletionChunk`

Если вы мигрируете большой application codepath, явные primary-импорты это хороший сигнал, что код действительно переведен на v2-контракт.

## Если вы пока остаетесь на legacy

Миграцию можно делать поэтапно. Если вы еще не готовы переносить payload и обработку ответа, переключитесь на явный `.legacy`.

```python
response = client.chat.legacy.create(payload)

for chunk in client.chat.legacy.stream(payload):
    ...

completion, parsed = client.chat.legacy.parse(
    payload,
    response_format=MathAnswer,
)
```

Для async-кода используется тот же подход через `client.achat.legacy`.

Это полезно, если:

- нужно сначала убрать deprecation warnings
- у вас много кода, который зависит от `choices[0].message.content`
- downstream-компоненты еще ожидают legacy usage fields или legacy chunk shape

Относитесь к `.legacy` как к режиму совместимости, а не как к финальной точке для нового кода.

## Чеклист миграции

Такой порядок удобно использовать при апгрейде приложения с v1 на v2:

1. Заменить deprecated root methods на явные resource methods.
2. Для каждого codepath решить, мигрирует ли он сразу на primary или временно уходит на `.legacy`.
3. В мигрируемых codepath заменить legacy request-модели на primary-модели.
4. Переписать чтение response с `choices`-подхода на `messages`-подход.
5. Обновить streaming consumers под primary chunks.
6. Заменить legacy alias-импорты на явные primary imports там, где имена конфликтуют.
7. Перевести structured output на `client.chat.parse()` / `client.achat.parse()`.
8. Повторно протестировать код, который зависит от tool calling, usage accounting и timestamp fields.

## Частые ошибки при миграции

- Переименовать `client.chat(...)` в `client.chat.create(...)`, но продолжать читать `response.choices[0].message.content`.
- Импортировать `ChatCompletionChunk` из `gigachat.models` и ожидать primary shape.
- Рассматривать v2 как расширение legacy payload поле-в-поле.
- Перевести sync-код на `client.chat.create()`, но оставить async-код на deprecated shim-ах.
- Передавать Pydantic-модель в legacy `create()` вместо перехода на `parse()`.

Если вы видите один из этих паттернов в ревью, значит миграция пока частичная.

## Примечания по совместимости

- Primary-модели специально сделаны терпимыми к расширению wire-format и принимают дополнительные поля.
- `tool_state_id` и `functions_state_id` поддерживаются как alias-ы для `tools_state_id`.
- В primary-ответах и stream-chunk-ах `created` поддерживается как alias для `created_at`.
- Старые top-level импорты legacy-моделей пока сохранены, но в новом коде лучше использовать primary-имена.
