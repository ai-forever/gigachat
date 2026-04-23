# PLANS.md

## Задача

Подготовить SDK к переходу на Resources API так, чтобы **старый chat API стал legacy-поверхностью**, а namespace `client.chat` / `client.achat` был освобождён под будущий основной surface для `v2/chat/completions`.

В этом PR **не нужно** реализовывать новый `v2/chat/completions`. Нужно только:

1. вынести текущий chat API под `.legacy`;
2. оставить обратную совместимость через deprecated shims;
3. перевести ресурсы клиента на `cached_property`;
4. обновить тесты и документацию.

## Правила исполнения

1. Выполнять задачи строго по очереди, в порядке из раздела `Предлагаемый порядок работы`.
2. В одном чате выполнять только одну задачу из плана.
3. После завершения каждого среза делать отдельный git-коммит.
4. Прогресс по плану вести в отдельном файле `docs/internal/PLANS_PROGRESS.md`.
5. Перед переходом к следующей задаче фиксировать в `docs/internal/PLANS_PROGRESS.md`, что текущий срез завершён.

---

## Что должно получиться снаружи

### Новый поддерживаемый legacy surface

```python
from gigachat import GigaChat

with GigaChat() as client:
    completion = client.chat.legacy.create("Hello")

    for chunk in client.chat.legacy.stream("Write a poem"):
        print(chunk.choices[0].delta.content, end="")

    completion, parsed = client.chat.legacy.parse(
        "Solve 8x+7=-23",
        response_format=MathResult,
    )
```

```python
import asyncio
from gigachat import GigaChat

async def main() -> None:
    async with GigaChat() as client:
        completion = await client.achat.legacy.create("Hello")

        async for chunk in client.achat.legacy.stream("Write a poem"):
            print(chunk.choices[0].delta.content, end="")

        completion, parsed = await client.achat.legacy.parse(
            "Solve 8x+7=-23",
            response_format=MathResult,
        )

asyncio.run(main())
```

### Обратная совместимость через deprecated shims

Эти вызовы должны продолжить работать, но выдавать `DeprecationWarning`:

```python
client.chat(...)         -> client.chat.legacy.create(...)
client.stream(...)       -> client.chat.legacy.stream(...)
client.chat_parse(...)   -> client.chat.legacy.parse(...)

await client.achat(...)       -> await client.achat.legacy.create(...)
client.astream(...)           -> client.achat.legacy.stream(...)
await client.achat_parse(...) -> await client.achat.legacy.parse(...)
```

### Важно

**Не добавляй** старому API новые entrypoints вроде `client.chat.create(...)`.

Причина: `client.chat` и `client.achat` должны стать namespace-объектами, под которыми позже появится **новая основная поверхность** для `v2/chat/completions` (например, `client.chat.completions...`).

В этом PR `client.chat` / `client.achat` — это namespace, в котором пока есть только `.legacy` и deprecated callable compatibility layer.

---

## Репозиторные ограничения, которые надо соблюдать

1. Python 3.8 compatibility обязательна:
   - использовать `typing.Optional`, `typing.Dict`, `typing.List`, `typing.Type`;
   - не использовать `X | Y` и builtin generics.
2. Не добавлять новых runtime dependencies.
3. Придерживаться существующего стиля SDK:
   - auth/retry decorators;
   - Pydantic V2 models;
   - ресурсы, которые держат ссылку на `_base_client`.
4. Новые resource-объекты должны создаваться через `functools.cached_property`.

---

## Текущее состояние, от которого надо отталкиваться

1. В `src/gigachat/client.py` сейчас живут root-методы:
   - sync: `chat`, `stream`, `chat_parse`;
   - async: `achat`, `astream`, `achat_parse`.
2. `assistants` / `threads` уже выглядят как resource-like subclients, но сейчас они создаются eagerly в конструкторах (`self.assistants = ...`, `self.threads = ...`, `self.a_assistants = ...`, `self.a_threads = ...`).
3. Тесты уже разбиты по клиентским поверхностям:
   - `tests/unit/gigachat/test_client_chat.py`
   - `tests/unit/gigachat/test_client_chat_parse.py`
   - `tests/unit/gigachat/test_client_assistants.py`
   - `tests/unit/gigachat/test_client_threads.py`
4. В `README.md` сейчас root chat methods ещё описаны как основной публичный API — это надо поменять.

---

## Архитектурное решение

### 1) Ввести namespace/resources для chat

Добавить новый пакет:

```text
src/gigachat/resources/
    __init__.py
    chat.py
```

В `src/gigachat/resources/chat.py` завести 4 класса:

- `ChatNamespace`
- `LegacyChatSyncResource`
- `AsyncChatNamespace`
- `LegacyChatAsyncResource`

### 2) `client.chat` и `client.achat` сделать `cached_property`

На клиентских классах должны появиться свойства:

```python
@cached_property
def chat(self) -> ChatNamespace: ...

@cached_property
def achat(self) -> AsyncChatNamespace: ...
```

`client.chat` и `client.achat` становятся **namespace-объектами**, а не обычными bound-method.

### 3) Совместимость через `__call__`

Чтобы старый код `client.chat(...)` / `await client.achat(...)` не сломался, реализуй:

```python
class ChatNamespace:
    def __call__(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion: ...

class AsyncChatNamespace:
    async def __call__(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion: ...
```

Оба `__call__` должны:

1. выдать `DeprecationWarning`;
2. делегировать в `.legacy.create(...)`.

### 4) Legacy resource должен быть единственным местом для старого chat API

```python
client.chat.legacy.create(...)
client.chat.legacy.stream(...)
client.chat.legacy.parse(...)

client.achat.legacy.create(...)
client.achat.legacy.stream(...)
client.achat.legacy.parse(...)
```

Именно это — новый канонический путь для старого API.

### 5) Не пытаться в этом PR строить новый v2 surface

Нужна только инфраструктура и освобождение namespace.

---

## Рекомендуемая реализация без лишнего риска

### Почему не стоит переносить всю старую chat-логику сразу в `resources/chat.py`

Сейчас helper-функции вроде:

- `_validate_response_format`
- `_parse_chat`
- `_prepare_chat_for_parse`
- `_parse_completion`

живут в `client.py`.

Если напрямую перетаскивать всё в новый resource module, легко получить циклические импорты и раздутый diff.

### Поэтому делай так

#### A. Оставь текущую low-level legacy chat-логику в `client.py`, но спрячь её в private methods

На `GigaChatSyncClient`:

- `_legacy_chat_create(...)`
- `_legacy_chat_stream(...)`
- `_legacy_chat_parse(...)`

На `GigaChatAsyncClient`:

- `_legacy_achat_create(...)`
- `_legacy_achat_stream(...)`
- `_legacy_achat_parse(...)`

#### B. Сохрани decorators на private helper methods

Сетевые вызовы должны оставаться под теми же декораторами, что и сейчас:

- sync request: `@_with_retry` + `@_with_auth`
- sync stream: `@_with_retry_stream` + `@_with_auth_stream`
- async request: `@_awith_retry` + `@_awith_auth`
- async stream: `@_awith_retry_stream` + `@_awith_auth_stream`

#### C. Resource classes пусть будут тонкими proxy-объектами

`LegacyChatSyncResource` и `LegacyChatAsyncResource` должны просто вызывать private helper methods базового клиента.

Это даст:

- новый resources surface;
- минимум дублирования;
- отсутствие double-wrapping auth/retry;
- минимальный риск рекурсий и циклических импортов.

---

## Конкретный план изменений по файлам

### 1. `src/gigachat/resources/chat.py`

Добавь namespace/resource classes.

Ожидаемая форма примерно такая:

```python
from __future__ import annotations

import warnings
from functools import cached_property
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, Iterator, Tuple, Type, TypeVar, Union

import pydantic

from gigachat.models import Chat, ChatCompletion, ChatCompletionChunk

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient

ModelT = TypeVar("ModelT", bound=pydantic.BaseModel)


class LegacyChatSyncResource:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    def create(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion:
        return self._base_client._legacy_chat_create(payload)

    def stream(self, payload: Union[Chat, Dict[str, Any], str]) -> Iterator[ChatCompletionChunk]:
        return self._base_client._legacy_chat_stream(payload)

    def parse(
        self,
        payload: Union[Chat, Dict[str, Any], str],
        *,
        response_format: Type[ModelT],
        strict: bool = True,
    ) -> Tuple[ChatCompletion, ModelT]:
        return self._base_client._legacy_chat_parse(
            payload,
            response_format=response_format,
            strict=strict,
        )


class ChatNamespace:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    @cached_property
    def legacy(self) -> LegacyChatSyncResource:
        return LegacyChatSyncResource(self._base_client)

    def __call__(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion:
        warnings.warn(
            "`client.chat(...)` is deprecated; use `client.chat.legacy.create(...)`.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.legacy.create(payload)
```

Async-ветка должна быть симметричной:

- `AsyncChatNamespace`
- `LegacyChatAsyncResource`
- у `AsyncChatNamespace.__call__` — `async def`
- `legacy.stream(...)` возвращает `AsyncIterator[ChatCompletionChunk]`

### 2. `src/gigachat/resources/__init__.py`

Экспортируй internal resource classes для импорта из `client.py`.

**Не нужно** добавлять их в публичный `gigachat.__init__`.

### 3. `src/gigachat/client.py`

#### 3.1. Импорты

Добавь:

- `warnings`
- `cached_property`
- imports из `gigachat.resources.chat`

#### 3.2. Переведи существующие subclients на `cached_property`

Сейчас в конструкторах sync/async клиента есть eager assignments:

```python
self.assistants = AssistantsSyncClient(self)
self.threads = ThreadsSyncClient(self)
self.a_assistants = AssistantsAsyncClient(self)
self.a_threads = ThreadsAsyncClient(self)
```

Их нужно убрать из `__init__` и заменить на class-level `cached_property`:

```python
@cached_property
def assistants(self) -> AssistantsSyncClient:
    return AssistantsSyncClient(self)

@cached_property
def threads(self) -> ThreadsSyncClient:
    return ThreadsSyncClient(self)

@cached_property
def a_assistants(self) -> AssistantsAsyncClient:
    return AssistantsAsyncClient(self)

@cached_property
def a_threads(self) -> ThreadsAsyncClient:
    return ThreadsAsyncClient(self)
```

И добавить:

```python
@cached_property
def chat(self) -> ChatNamespace:
    return ChatNamespace(self)

@cached_property
def achat(self) -> AsyncChatNamespace:
    return AsyncChatNamespace(self)
```

#### 3.3. Убери public root `chat()` method как метод класса

`client.chat` должен стать `cached_property`, а не методом.

Значит:

- старый `def chat(...)` больше не должен существовать как обычный метод;
- compat path должен идти через `ChatNamespace.__call__`.

#### 3.4. Введи private helper methods для legacy chat логики

На sync-клиенте:

```python
@_with_retry
@_with_auth
def _legacy_chat_create(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion: ...

@_with_retry_stream
@_with_auth_stream
def _legacy_chat_stream(self, payload: Union[Chat, Dict[str, Any], str]) -> Iterator[ChatCompletionChunk]: ...

def _legacy_chat_parse(
    self,
    payload: Union[Chat, Dict[str, Any], str],
    *,
    response_format: Type[ModelT],
    strict: bool = True,
) -> Tuple[ChatCompletion, ModelT]: ...
```

На async-клиенте:

```python
@_awith_retry
@_awith_auth
async def _legacy_achat_create(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion: ...

@_awith_retry_stream
@_awith_auth_stream
def _legacy_achat_stream(self, payload: Union[Chat, Dict[str, Any], str]) -> AsyncIterator[ChatCompletionChunk]: ...

async def _legacy_achat_parse(
    self,
    payload: Union[Chat, Dict[str, Any], str],
    *,
    response_format: Type[ModelT],
    strict: bool = True,
) -> Tuple[ChatCompletion, ModelT]: ...
```

Содержимое этих helper methods должно быть максимально близко к текущей реализации root methods.

#### 3.5. Оставь deprecated shims для `stream`, `chat_parse`, `astream`, `achat_parse`

Они должны остаться публичными методами клиента, но без сетевой логики внутри.

Примерно так:

```python
def stream(self, payload: Union[Chat, Dict[str, Any], str]) -> Iterator[ChatCompletionChunk]:
    warnings.warn(
        "`client.stream(...)` is deprecated; use `client.chat.legacy.stream(...)`.",
        DeprecationWarning,
        stacklevel=2,
    )
    return self.chat.legacy.stream(payload)
```

```python
def chat_parse(...):
    warnings.warn(
        "`client.chat_parse(...)` is deprecated; use `client.chat.legacy.parse(...)`.",
        DeprecationWarning,
        stacklevel=2,
    )
    return self.chat.legacy.parse(...)
```

```python
def astream(self, payload: Union[Chat, Dict[str, Any], str]) -> AsyncIterator[ChatCompletionChunk]:
    warnings.warn(
        "`client.astream(...)` is deprecated; use `client.achat.legacy.stream(...)`.",
        DeprecationWarning,
        stacklevel=2,
    )
    return self.achat.legacy.stream(payload)
```

```python
async def achat_parse(...):
    warnings.warn(
        "`client.achat_parse(...)` is deprecated; use `client.achat.legacy.parse(...)`.",
        DeprecationWarning,
        stacklevel=2,
    )
    return await self.achat.legacy.parse(...)
```

#### 3.6. Обнови текст ошибки в `_validate_response_format(...)`

Сейчас он отправляет пользователя в `client.chat_parse(...)`.

Это надо заменить на что-то вроде:

```python
"You tried to pass a Pydantic model to `chat(response_format=...)`; "
"use `client.chat.legacy.parse(...)` or `client.achat.legacy.parse(...)` instead"
```

Это важно, потому что иначе SDK сам будет советовать deprecated surface.

#### 3.7. Обнови docstrings

Минимум:

- deprecated shim methods должны явно помечаться как deprecated;
- новый legacy surface должен описываться как legacy namespace;
- везде, где сейчас `chat_parse` описан как канонический structured-output путь, переключить ссылки на `.legacy.parse(...)`.

### 4. `src/gigachat/__init__.py`

Скорее всего менять ничего не нужно, если resource classes не должны быть публично импортируемыми напрямую.

Если возникнет соблазн экспортировать `ChatNamespace` / `LegacyChatSyncResource` наружу — **не делай этого** в этом PR.

### 5. `README.md`

Обязательно обнови примеры:

- Basic chat → `client.chat.legacy.create(...)`
- Streaming → `client.chat.legacy.stream(...)`
- Async → `await client.achat.legacy.create(...)`, `client.achat.legacy.stream(...)`
- Structured output → `client.chat.legacy.parse(...)`

Добавь отдельный migration note, где будет явно сказано:

- root methods ещё работают;
- они deprecated;
- legacy path — новый канонический путь для старого chat API;
- namespace `client.chat` / `client.achat` зарезервирован под будущий `v2/chat/completions`.

### 6. `examples/README.md` и/или примеры

Если где-то явно используются `chat()`, `stream()`, `chat_parse()`, переведи примеры на `.legacy` surface.

Не обязательно менять вообще все интеграционные notebook-файлы в этом PR, если это слишком широкий шум, но минимум текстовые docs/examples должны быть согласованы с новым публичным API.

---

## Тестовый план

### A. Существующие тесты не должны потерять coverage старого поведения

Сохрани текущие проверки для:

- chat request body;
- stream parsing;
- chat_parse structured output;
- async equivalents.

### B. Добавь новые тесты на ресурсы

Можно создать новый файл, например:

```text
tests/unit/gigachat/test_client_resources.py
```

Или аккуратно добавить проверки в существующие test files.

### Обязательные новые тесты

#### 1. Legacy resources работают без warning

- `client.chat.legacy.create(...)`
- `client.chat.legacy.stream(...)`
- `client.chat.legacy.parse(...)`
- `await client.achat.legacy.create(...)`
- `client.achat.legacy.stream(...)`
- `await client.achat.legacy.parse(...)`

Они должны работать и **не** выдавать `DeprecationWarning`.

#### 2. Deprecated compatibility shims предупреждают

Используй `pytest.warns(DeprecationWarning)` для:

- `client.chat(...)`
- `client.stream(...)`
- `client.chat_parse(...)`
- `await client.achat(...)`
- `client.astream(...)`
- `await client.achat_parse(...)`

И обязательно проверь, что результат у них тот же тип, что и раньше.

#### 3. `cached_property` действительно кеширует ресурс

Проверь identity:

```python
assert client.chat is client.chat
assert client.assistants is client.assistants
assert client.threads is client.threads
```

Async-аналогично:

```python
assert client.achat is client.achat
assert client.a_assistants is client.a_assistants
assert client.a_threads is client.a_threads
```

#### 4. `client.chat` остаётся callable

Проверить, что:

```python
response = client.chat("text")
```

работает через `ChatNamespace.__call__` и выдаёт warning.

Async-аналогично:

```python
response = await client.achat("text")
```

#### 5. `chat_parse`/`achat_parse` deprecated shims не ломают parse semantics

Проверить, что через deprecated surface всё ещё:

- строится `response_format` JSON Schema;
- сохраняется `strict=True/False`;
- поднимаются те же ошибки (`LengthFinishReasonError`, `ValidationError`, `JSONDecodeError`).

### C. Что прогнать локально

Минимум:

```bash
make fmt
make mypy
make test
```

Если есть время — дополнительно targeted runs:

```bash
uv run pytest tests/unit/gigachat/test_client_chat.py
uv run pytest tests/unit/gigachat/test_client_chat_parse.py
uv run pytest tests/unit/gigachat/test_client_assistants.py
uv run pytest tests/unit/gigachat/test_client_threads.py
```

---

## Acceptance criteria

PR считается успешным, если выполнено всё ниже:

1. `client.chat` и `client.achat` — это resource namespaces на `cached_property`.
2. У них есть `.legacy` subresource.
3. Старый chat API доступен по:
   - `client.chat.legacy.create/stream/parse`
   - `client.achat.legacy.create/stream/parse`
4. Старые root entrypoints продолжают работать:
   - `client.chat(...)`
   - `client.stream(...)`
   - `client.chat_parse(...)`
   - `await client.achat(...)`
   - `client.astream(...)`
   - `await client.achat_parse(...)`
5. Все 6 root entrypoints выдают `DeprecationWarning` с `stacklevel=2`.
6. `client.chat.legacy.*` и `client.achat.legacy.*` warning не выдают.
7. `assistants`, `threads`, `a_assistants`, `a_threads` тоже переведены на `cached_property`.
8. README/documentation больше не рекламируют root chat methods как основной API.
9. Никакой реализации нового `v2/chat/completions` в этом PR нет.
10. `make fmt`, `make mypy`, `make test` проходят.

---

## Нюансы и ловушки

### 1. Не задвоить auth/retry

Если deprecated shim вызывает уже decorated private helper/resource method, сам shim **не должен** тоже быть decorated, иначе можно получить лишний retry/auth layer.

### 2. Не уйти в рекурсию

Нельзя делать так, чтобы:

- `chat_parse()` вызывал `self.chat(...)`,
- `self.chat(...)` шёл в `__call__`,
- `__call__` шёл в `.legacy.create()`,
- а `.legacy.create()` снова использовал deprecated surface.

Legacy resource должен опираться только на private helper methods или на прямой API call, но не на deprecated public path.

### 3. Не сломать async stream тип

`client.astream(...)` и `client.achat.legacy.stream(...)` должны возвращать `AsyncIterator[ChatCompletionChunk]`, а не coroutine с list/tuple.

### 4. Возможная поведенческая разница: `client.chat` больше не bound-method

Обычный пользовательский код вида `client.chat("...")` продолжит работать.
Но код, который ожидает, что `client.chat` — именно `MethodType`, теоретически изменится.

Это допустимо для такого рефакторинга, но:

- не ломай обычный callable behavior;
- зафиксируй это в migration note.

### 5. Тексты ошибок/подсказок должны вести в `.legacy`, а не в deprecated root methods

Особенно важно для `_validate_response_format(...)`.

---

## Что НЕ делать в этом PR

1. Не реализовывать `client.chat.create(...)` для старого API.
2. Не реализовывать `client.chat.completions` или `client.achat.completions`.
3. Не переделывать все endpoint groups в новую иерархию за один раз.
4. Не экспортировать новые resource classes через top-level `gigachat.__init__` без необходимости.
5. Не добавлять runtime dependencies ради resources.

---

## Предлагаемый порядок работы

1. Создать `resources/chat.py` и `resources/__init__.py`.
2. Добавить `cached_property` namespaces/resources в client classes.
3. Вынести текущую legacy chat-логику в private helper methods.
4. Перевести `assistants` / `threads` / `a_assistants` / `a_threads` на `cached_property`.
5. Добавить deprecated shims.
6. Обновить error messages/docstrings.
7. Обновить README/examples.
8. Добавить/обновить unit tests.
9. Прогнать `make fmt`, `make mypy`, `make test`.

---

## После этого PR можно будет отдельно делать следующий шаг

Следующим PR уже можно спокойно сажать новый основной surface под освобождённый namespace, например:

- `client.chat.completions.create(...)`
- `client.chat.completions.stream(...)`
- `client.achat.completions.create(...)`
- `client.achat.completions.stream(...)`

Но **не сейчас**. Текущий PR — только groundwork и migration of old surface into `legacy`.
