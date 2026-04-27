# План: добить Resource API для всех non-chat поверхностей

## Контекст

PR `#109` сейчас в статусе draft и вносит `feature/resource_api_v2` в `feature/resource_api`. По описанию PR уже добавляет primary `chat/completions` v2, legacy chat namespaces, streaming, parse flows, docs/examples/tests и migration guides.

В текущей ветке `src/gigachat/resources/` содержит только `__init__.py` и `chat.py`, то есть ресурсная архитектура фактически доведена только для chat namespace. При этом в `client.py` остаются root-методы для non-chat операций: `tokens_count`, `embeddings`, `get_models`, `get_model`, `get_image`, file CRUD, `get_balance`, `openapi_function_convert`, `check_ai` и async-аналоги.

Цель этого плана: **перевести всё остальное на resource API**, не трогая уже сделанные chat v1 legacy и chat v2 primary surfaces, кроме минимальных import/test fallout. Дальше работаем строго маленькими срезами.

---

## Главные правила для GPT-5.5 Codex

1. **Один заход = одна задача = один срез из этого плана.**
   Нельзя брать следующий срез, даже если текущий кажется маленьким.

2. **Каждый срез заканчивается отдельным commit.**
   Формат commit message: `<type>(resources): <short description>`.

3. **Прогресс обязателен.**
   Перед commit обновить `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.

4. **Не менять chat v1/v2 surface.**
   Не переделывать:
   - `client.chat.create/stream/parse`
   - `client.achat.create/stream/parse`
   - `client.chat.legacy.*`
   - `client.achat.legacy.*`
   - deprecated chat shims

5. **Старые root-методы не удалять.**
   Они должны остаться deprecated compatibility shims и делегировать в новые resources.

6. **Deprecated shims должны выдавать `DeprecationWarning`.**
   Warning должен указывать новый resource path.

7. **Новые resource methods warning не выдают.**

8. **Не добавлять runtime dependencies.**

9. **Сохранять Python 3.8 compatibility.**
   Использовать `Optional`, `List`, `Dict`, `Tuple`, `Union`, `Type`.
   Не использовать `X | Y` и builtin generics вроде `list[str]`.

10. **Не менять wire contract и URLs.**
    Resource layer — это публичная клиентская поверхность, не новая логика транспорта.

---

## Целевая публичная surface

| Старый sync path | Новый sync resource path | Старый async path | Новый async resource path |
|---|---|---|---|
| `client.get_models()` | `client.models.list()` | `await client.aget_models()` | `await client.a_models.list()` |
| `client.get_model(model)` | `client.models.retrieve(model)` | `await client.aget_model(model)` | `await client.a_models.retrieve(model)` |
| `client.embeddings(texts, model=...)` | `client.embeddings.create(texts, model=...)` | `await client.aembeddings(texts, model=...)` | `await client.a_embeddings.create(texts, model=...)` |
| `client.upload_file(file, purpose=...)` | `client.files.upload(file, purpose=...)` | `await client.aupload_file(file, purpose=...)` | `await client.a_files.upload(file, purpose=...)` |
| `client.get_file(file)` | `client.files.retrieve(file)` | `await client.aget_file(file)` | `await client.a_files.retrieve(file)` |
| `client.get_files()` | `client.files.list()` | `await client.aget_files()` | `await client.a_files.list()` |
| `client.delete_file(file)` | `client.files.delete(file)` | `await client.adelete_file(file)` | `await client.a_files.delete(file)` |
| `client.get_image(file_id)` | `client.files.retrieve_image(file_id)` | `await client.aget_image(file_id)` | `await client.a_files.retrieve_image(file_id)` |
| `client.tokens_count(input_, model=...)` | `client.tokens.count(input_, model=...)` | `await client.atokens_count(input_, model=...)` | `await client.a_tokens.count(input_, model=...)` |
| `client.get_balance()` | `client.balance.get()` | `await client.aget_balance()` | `await client.a_balance.get()` |
| `client.openapi_function_convert(openapi_function)` | `client.functions.convert_openapi(openapi_function)` | `await client.aopenapi_function_convert(openapi_function)` | `await client.a_functions.convert_openapi(openapi_function)` |
| `client.check_ai(text, model)` | `client.ai_check.check(text, model)` | `await client.acheck_ai(text, model)` | `await client.a_ai_check.check(text, model)` |

### Особый случай: `client.embeddings`

`client.embeddings` уже занят старым callable API. Переводить его как chat:

```python
client.embeddings.create(...)
client.embeddings(...)  # deprecated callable shim через __call__
```

Для async не создавать `client.aembeddings` namespace, чтобы не конфликтовать с текущим method name. Новый async resource path:

```python
await client.a_embeddings.create(...)
await client.aembeddings(...)  # deprecated root shim
```

---

## Файлы плана и прогресса

Создать и вести:

```text
docs/internal/RESOURCE_API_REMAINING_PLAN.md
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

Формат progress file:

```md
# Resource API Remaining Progress

План: docs/internal/RESOURCE_API_REMAINING_PLAN.md

## Правила

- Один заход = один срез.
- Один срез = один commit.
- Перед commit обновлять этот файл.
- Нельзя начинать следующий срез в том же заходе.

## Срезы

1. [todo] Restore plan/progress docs
2. [todo] Add shared resource deprecation helper
3. [todo] Normalize assistants resource module
4. [todo] Normalize threads resource module
5. [todo] Add models resource
6. [todo] Add embeddings resource
7. [todo] Add files resource
8. [todo] Add tokens resource
9. [todo] Add balance resource
10. [todo] Add functions resource
11. [todo] Add ai_check resource
12. [todo] Update docs/examples for non-chat resources
13. [todo] Add global resource/shim regression tests
14. [todo] Final audit and cleanup

## Журнал

- 2026-04-27: план создан.
```

Каждый завершённый срез должен добавлять запись:

```md
- 2026-04-27: завершён срез N.
  - Что сделано:
  - Изменённые файлы:
  - Тесты:
  - Commit:
  - Замечания:
```

---

## Definition of Done для любого среза

Срез можно закрыть только если:

1. Сделана ровно одна задача из списка.
2. Новый resource path работает.
3. Старый root path работает как deprecated shim.
4. Deprecated shim покрыт тестом на `DeprecationWarning`.
5. Новый resource path покрыт тестом на отсутствие warning.
6. Resource property создаётся через `cached_property`, если это namespace на клиенте.
7. Нет double auth/retry wrapping.
8. Прогресс записан в `RESOURCE_API_REMAINING_PROGRESS.md`.
9. Сделан commit.
10. В ответе пользователю указан прогресс: срез, commit, тесты.

---

# Срезы и commit-план

## Срез 1 — восстановить plan/progress docs

**Commit:** `docs(resources): add remaining resource api plan`

**Задача:** добавить план и progress file.

**Файлы:**

```text
docs/internal/RESOURCE_API_REMAINING_PLAN.md
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Добавить этот план в `RESOURCE_API_REMAINING_PLAN.md`.
- Добавить progress template в `RESOURCE_API_REMAINING_PROGRESS.md`.
- Отметить срез 1 как `[done]`.

**Тесты:**

```bash
git diff --check
```

**Не делать:**

- Не менять Python-код.
- Не начинать следующий срез.

---

## Срез 2 — добавить shared helper для deprecated resource shims

**Commit:** `refactor(resources): add deprecated resource shim helper`

**Задача:** завести общий helper для warning-ов non-chat root shims.

**Файлы:**

```text
src/gigachat/resources/_utils.py
src/gigachat/resources/__init__.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Добавить helper:

```python
def warn_deprecated_resource_api(old_path: str, new_path: str) -> None:
    ...
```

- Использовать `DeprecationWarning`.
- `stacklevel` выбрать так, чтобы warning указывал на пользовательский call site.
- Не переподключать chat shims в этом срезе, чтобы не трогать chat v1/v2.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_chat.py -q
git diff --check
```

**Не делать:**

- Не добавлять новые resources.
- Не менять `client.py`, кроме import fallout, если он реально нужен.

---

## Срез 3 — нормализовать assistants resource module

**Commit:** `refactor(resources): move assistants resource into resources package`

**Задача:** перенести assistants resource-классы в `src/gigachat/resources/assistants.py`.

**Файлы:**

```text
src/gigachat/assistants.py
src/gigachat/resources/assistants.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_assistants.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Переместить `AssistantsSyncClient` / `AssistantsAsyncClient` в `gigachat.resources.assistants`.
- Старый `gigachat.assistants` оставить compatibility module, если внешний import мог использоваться.
- Public API не менять:
  - `client.assistants.*`
  - `client.a_assistants.*`
- Проверить, что `client.assistants` и `client.a_assistants` остаются `cached_property`.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_assistants.py -q
uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q
```

**Не делать:**

- Не менять методы assistants.
- Не трогать threads.

---

## Срез 4 — нормализовать threads resource module

**Commit:** `refactor(resources): move threads resource into resources package`

**Задача:** перенести threads resource-классы в `src/gigachat/resources/threads.py`.

**Файлы:**

```text
src/gigachat/threads.py
src/gigachat/resources/threads.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_threads.py
tests/unit/gigachat/test_client_lifecycle.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Переместить `ThreadsSyncClient` / `ThreadsAsyncClient` в `gigachat.resources.threads`.
- Старый `gigachat.threads` оставить compatibility module, если внешний import мог использоваться.
- Public API не менять:
  - `client.threads.*`
  - `client.a_threads.*`

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_threads.py -q
uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q
```

**Не делать:**

- Не менять assistants.
- Не менять chat.

---

## Срез 5 — добавить models resource

**Commit:** `feat(resources): add models resource`

**Задача:** перевести models API на resource namespace.

**Новая surface:**

```python
client.models.list()
client.models.retrieve(model)

await client.a_models.list()
await client.a_models.retrieve(model)
```

**Deprecated shims:**

```python
client.get_models()
client.get_model(model)

await client.aget_models()
await client.aget_model(model)
```

**Файлы:**

```text
src/gigachat/resources/models.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_models.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Добавить `ModelsSyncResource`.
- Добавить `ModelsAsyncResource`.
- В `client.py` добавить:
  - `@cached_property def models(...)`
  - `@cached_property def a_models(...)`
- Старые methods сделать deprecated shims.
- Shims не должны иметь auth/retry decorators, если вызывают уже decorated resource methods.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_models.py -q
uv run pytest tests/unit/gigachat/api/test_models.py -q
```

Если `test_models.py` ещё нет — создать только client-level тесты в этом срезе, а отсутствие api test отметить в progress.

**Не делать:**

- Не менять embeddings/files/tools.
- Не менять API transport.

---

## Срез 6 — добавить embeddings resource

**Commit:** `feat(resources): add embeddings resource`

**Задача:** перевести embeddings API на resource namespace.

**Новая surface:**

```python
client.embeddings.create(texts, model="Embeddings")
await client.a_embeddings.create(texts, model="Embeddings")
```

**Deprecated shims:**

```python
client.embeddings(texts, model="Embeddings")
await client.aembeddings(texts, model="Embeddings")
```

**Файлы:**

```text
src/gigachat/resources/embeddings.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_embeddings.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- `client.embeddings` сделать namespace с `create(...)`.
- Для backwards compatibility реализовать `EmbeddingsSyncResource.__call__(...)`.
- `client.a_embeddings` сделать async namespace.
- `client.aembeddings(...)` оставить deprecated async shim в `client.py`.
- Проверить, что default model остаётся `"Embeddings"`.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_embeddings.py -q
uv run pytest tests/unit/gigachat/api/test_embeddings.py -q
```

**Не делать:**

- Не менять models.
- Не менять chat.
- Не переименовывать модель `Embeddings`.

---

## Срез 7 — добавить files resource

**Commit:** `feat(resources): add files resource`

**Задача:** перевести file/image операции на resource namespace.

**Новая surface:**

```python
client.files.upload(file, purpose="general")
client.files.retrieve(file)
client.files.list()
client.files.delete(file)
client.files.retrieve_image(file_id)

await client.a_files.upload(file, purpose="general")
await client.a_files.retrieve(file)
await client.a_files.list()
await client.a_files.delete(file)
await client.a_files.retrieve_image(file_id)
```

**Deprecated shims:**

```python
client.upload_file(...)
client.get_file(...)
client.get_files()
client.delete_file(...)
client.get_image(...)

await client.aupload_file(...)
await client.aget_file(...)
await client.aget_files()
await client.adelete_file(...)
await client.aget_image(...)
```

**Файлы:**

```text
src/gigachat/resources/files.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_files.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Добавить `FilesSyncResource`.
- Добавить `FilesAsyncResource`.
- Root shims должны только warn + delegate.
- Сохранить `purpose: Literal["general", "assistant"] = "general"`.
- Проверить, что file object typing не ломается.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_files.py -q
uv run pytest tests/unit/gigachat/api/test_files.py -q
```

**Не делать:**

- Не менять assistants file APIs.
- Не менять upload transport.

---

## Срез 8 — добавить tokens resource

**Commit:** `feat(resources): add tokens resource`

**Задача:** перевести token counting на resource namespace.

**Новая surface:**

```python
client.tokens.count(input_, model=None)
await client.a_tokens.count(input_, model=None)
```

**Deprecated shims:**

```python
client.tokens_count(input_, model=None)
await client.atokens_count(input_, model=None)
```

**Файлы:**

```text
src/gigachat/resources/tokens.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_tokens.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Добавить `TokensSyncResource`.
- Добавить `TokensAsyncResource`.
- Сохранить default model fallback:
  - если `model is None`, использовать `self._settings.model or GIGACHAT_MODEL`.
- Старые root methods сделать deprecated shims.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_tokens.py -q
uv run pytest tests/unit/gigachat/api/test_tools.py -q
```

**Не делать:**

- Не трогать balance/functions/ai_check в этом срезе, даже если они лежат в `api/tools.py`.

---

## Срез 9 — добавить balance resource

**Commit:** `feat(resources): add balance resource`

**Задача:** перевести balance endpoint на resource namespace.

**Новая surface:**

```python
client.balance.get()
await client.a_balance.get()
```

**Deprecated shims:**

```python
client.get_balance()
await client.aget_balance()
```

**Файлы:**

```text
src/gigachat/resources/balance.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_balance.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Добавить sync/async balance resources.
- Сохранить поведение 403/ошибок как в текущем transport.
- Root shims только warn + delegate.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_balance.py -q
uv run pytest tests/unit/gigachat/api/test_tools.py -q
```

**Не делать:**

- Не менять token counting.
- Не менять function convert.

---

## Срез 10 — добавить functions resource

**Commit:** `feat(resources): add functions resource`

**Задача:** перевести OpenAPI function conversion на resource namespace.

**Новая surface:**

```python
client.functions.convert_openapi(openapi_function)
await client.a_functions.convert_openapi(openapi_function)
```

**Deprecated shims:**

```python
client.openapi_function_convert(openapi_function)
await client.aopenapi_function_convert(openapi_function)
```

**Файлы:**

```text
src/gigachat/resources/functions.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_functions.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Добавить `FunctionsSyncResource`.
- Добавить `FunctionsAsyncResource`.
- Метод назвать `convert_openapi`, не `openapi_function_convert`, чтобы resource API был читаемым.
- Старое имя оставить только deprecated shim.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_functions.py -q
uv run pytest tests/unit/gigachat/api/test_tools.py -q
```

**Не делать:**

- Не менять chat function calling models.
- Не менять `Function` / `FunctionParameters`.

---

## Срез 11 — добавить ai_check resource

**Commit:** `feat(resources): add ai check resource`

**Задача:** перевести AI detection endpoint на resource namespace.

**Новая surface:**

```python
client.ai_check.check(text, model)
await client.a_ai_check.check(text, model)
```

**Deprecated shims:**

```python
client.check_ai(text, model)
await client.acheck_ai(text, model)
```

**Файлы:**

```text
src/gigachat/resources/ai_check.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_ai_check.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Добавить sync/async resources.
- Сохранить сигнатуру `text: str, model: str`.
- Старые root methods сделать deprecated shims.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_ai_check.py -q
uv run pytest tests/unit/gigachat/api/test_tools.py -q
```

**Не делать:**

- Не менять examples в этом срезе.
- Не менять unrelated tools endpoints.

---

## Срез 12 — обновить docs/examples для non-chat resources

**Commit:** `docs(resources): document non-chat resource api`

**Задача:** обновить публичную документацию и runnable examples для non-chat resource paths.

**Файлы-кандидаты:**

```text
README.md
MIGRATION_GUIDE.md
MIGRATION_GUIDE_ru.md
examples/README.md
examples/files/*
examples/structured_outputs/*
examples/tools/*
examples/chat_completions/*  # только если есть non-chat root calls
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что сделать:**

- Заменить non-chat root calls на новые resource calls.
- В migration guide добавить таблицу non-chat replacements.
- Старые root calls описать как deprecated compatibility shims.
- Не переписывать chat migration заново.

**Паттерны для поиска:**

```bash
rg "get_models|get_model|embeddings\(|aembeddings\(|upload_file|get_file|get_files|delete_file|get_image|tokens_count|get_balance|openapi_function_convert|check_ai|aget_models|aget_model|aupload_file|aget_file|aget_files|adelete_file|aget_image|atokens_count|aget_balance|aopenapi_function_convert|acheck_ai" README.md MIGRATION_GUIDE*.md examples tests
```

**Тесты:**

```bash
uv run pytest tests/unit/examples -q
git diff --check
```

**Не делать:**

- Не менять API-код.
- Не менять chat docs, кроме случайных non-chat references.

---

## Срез 13 — добавить global resource/shim regression tests

**Commit:** `test(resources): cover non-chat resource shims`

**Задача:** добавить общий regression matrix, который доказывает, что все non-chat root shims deprecated, а resource paths canonical.

**Файлы:**

```text
tests/unit/gigachat/test_client_resource_shims.py
tests/unit/gigachat/test_client_lifecycle.py
docs/internal/RESOURCE_API_REMAINING_PROGRESS.md
```

**Что покрыть:**

- `client.models is client.models`
- `client.a_models is client.a_models`
- `client.embeddings is client.embeddings`
- `client.files is client.files`
- `client.tokens is client.tokens`
- `client.balance is client.balance`
- `client.functions is client.functions`
- `client.ai_check is client.ai_check`
- async resource properties cached too.
- Каждый deprecated root shim выдаёт `DeprecationWarning`.
- Каждый новый resource path warning не выдаёт.
- Deprecated shims делегируют в те же low-level APIs, что и resource methods.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_resource_shims.py -q
uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q
```

**Не делать:**

- Не менять production-код, кроме исправлений, прямо обнаруженных этими тестами.
- Не добавлять новые resource names.

---

## Срез 14 — final audit and cleanup

**Commit:** `chore(resources): finish non-chat resource api migration`

**Задача:** финальная проверка, что non-chat root API больше не рекламируется как canonical.

**Что проверить:**

```bash
rg "client\.get_models|client\.get_model|client\.embeddings\(|client\.aembeddings\(|client\.upload_file|client\.get_file|client\.get_files|client\.delete_file|client\.get_image|client\.tokens_count|client\.get_balance|client\.openapi_function_convert|client\.check_ai|client\.aget_models|client\.aget_model|client\.aupload_file|client\.aget_file|client\.aget_files|client\.adelete_file|client\.aget_image|client\.atokens_count|client\.aget_balance|client\.aopenapi_function_convert|client\.acheck_ai" .
```

Допустимые совпадения:

- tests for deprecated shims
- migration guides
- progress/plan docs

**Финальные команды:**

```bash
uv run ruff check .
uv run pytest
make mypy
git diff --check
```

**Что сделать в progress:**

- Записать полный список финальных команд.
- Если команда не прошла, не коммитить финальный срез до исправления.
- Если какая-то команда не может быть запущена локально, явно записать причину.

**Не делать:**

- Не начинать новые фичи.
- Не менять chat v1/v2.
- Не удалять deprecated shims.

---

## Acceptance criteria всей работы

Работа считается завершённой, если:

1. Все non-chat операции доступны через resource namespaces.
2. Chat v1 legacy и chat v2 primary surfaces остались без архитектурного переписывания.
3. Все старые non-chat root methods работают как deprecated shims.
4. Все deprecated shims покрыты warning-тестами.
5. Новые resource methods покрыты тестами без warning.
6. Все resource namespaces на клиенте ленивые и кешируются через `cached_property`.
7. `client.py` больше не разрастается новой endpoint-логикой.
8. README/examples показывают resource API как canonical.
9. Migration guides содержат mapping старых non-chat методов на новые resource paths.
10. `uv run ruff check .`, `uv run pytest`, `make mypy`, `git diff --check` проходят.
11. `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md` содержит журнал каждого среза и commit hash.

---

## Ответ Codex после каждого среза

После каждого захода ответ должен быть в таком формате:

```md
## Прогресс

Срез: N — <название>
Статус: done
Commit: <hash> <message>

Что сделано:
- ...

Тесты:
- `...` — passed

Что осталось:
- следующий срез: N+1 — <название>
```

Не писать “заодно сделал следующий срез”. Если следующий срез тоже нужен, он делается отдельным заходом.
