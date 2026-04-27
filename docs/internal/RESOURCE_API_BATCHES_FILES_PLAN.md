# GPT-5.5 Codex plan: перенести batches/files/function-validation на Resource API

Дата плана: 2026-04-27

## Контекст

Базовая ветка для работы: `feature/resource-api-non-chat` / PR `#110`, либо ветка, которая уже содержит изменения PR `#110` поверх `feature/resource_api_v2`.

Источник для переноса: `feature/v2_completions` и связанный draft PR `#102` (`feat: add batch API support`).

PR `#110` уже переводит основные non-chat endpoints на resource namespaces: `models`, `embeddings`, `files`, `tokens`, `balance`, `functions.convert_openapi`, `ai_check`, плюс переносит `assistants`/`threads` в `gigachat.resources`. В этом follow-up не надо повторять эти срезы.

Что нужно добрать из `feature/v2_completions`:

1. `batches`: модели, low-level API helpers, client methods, тесты, фикстуры, пример.
2. `files`: не только CRUD, а именно `get_file_content` / `aget_file_content`, модель `File`, deprecated alias `get_image` / `aget_image`.
3. Забытый non-chat endpoint: `/functions/validate`, `FunctionValidationResult`, `FunctionValidationIssue`, client methods `validate_function` / `avalidate_function`.

## Жёсткие правила для GPT-5.5 Codex

1. Один заход = одна задача = один срез ниже.
2. Нельзя брать следующий срез в том же заходе, даже если текущий маленький.
3. Каждый срез заканчивается отдельным commit.
4. Перед commit обязательно обновить progress-файл.
5. В ответе после среза обязательно написать прогресс по шаблону из раздела «Формат ответа после каждого среза».
6. Не переписывать chat v1/v2 surface.
7. Старые root methods не удалять: они должны стать deprecated compatibility shims.
8. Новые canonical resource methods не должны выдавать `DeprecationWarning`.
9. Deprecated shims и compatibility aliases должны выдавать `DeprecationWarning` с указанием нового resource path.
10. Не добавлять runtime dependencies.
11. Сохранять Python 3.8 compatibility: `Optional`, `List`, `Dict`, `Tuple`, `Union`, `Type`; не использовать `X | Y` и `list[str]`.
12. Не менять wire contract и URLs без отдельного среза и явной причины.
13. Не делать version bump, если это не отдельное указание релизного процесса. В PR `#102` был bump, но в этом плане его не переносим автоматически.
14. Не добавлять «заодно» cleanup, docs, examples или тесты из следующего среза.

## Progress-файл

Создать и вести:

```text
docs/internal/RESOURCE_API_BATCHES_FILES_PLAN.md
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

`RESOURCE_API_BATCHES_FILES_PLAN.md` должен содержать этот план.

`RESOURCE_API_BATCHES_FILES_PROGRESS.md` должен быть в таком формате:

```md
# Resource API Batches/Files Progress

План: docs/internal/RESOURCE_API_BATCHES_FILES_PLAN.md

## Правила

- Один заход = один срез.
- Один срез = один commit.
- Перед commit обновлять этот файл.
- Нельзя начинать следующий срез в том же заходе.

## Срезы

1. [todo] Add follow-up plan/progress docs
2. [todo] Add low-level batches API and models
3. [todo] Add batches resource namespace and deprecated root shims
4. [todo] Add batch example/docs on resource paths
5. [todo] Add low-level file content API and File model
6. [todo] Add files.retrieve_content resource path and shims
7. [todo] Add low-level function validation API and models
8. [todo] Add functions.validate resource path and shims
9. [todo] Add global resource/shim regression coverage
10. [todo] Update public docs and migration guides
11. [todo] Final audit and cleanup

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

## Целевая публичная surface

### Batches

| Legacy/root path | Canonical resource path |
|---|---|
| `client.create_batch(file, method)` | `client.batches.create(file, method)` |
| `client.get_batches()` | `client.batches.list()` |
| `client.get_batches(batch_id="...")` | `client.batches.retrieve("...")` |
| `await client.acreate_batch(file, method)` | `await client.a_batches.create(file, method)` |
| `await client.aget_batches()` | `await client.a_batches.list()` |
| `await client.aget_batches(batch_id="...")` | `await client.a_batches.retrieve("...")` |

Важно: в переносимой реализации `get_batches(batch_id=...)` возвращает `Batches`, а не `Batch`, потому что single payload нормализуется в `{"batches": [payload]}`. В этом плане сохранить этот контракт; не менять return type на `Batch` в том же заходе.

### Files content

| Legacy/root path | Canonical resource path |
|---|---|
| `client.get_file_content(file_id)` | `client.files.retrieve_content(file_id)` |
| `client.get_image(file_id)` | `client.files.retrieve_content(file_id)` |
| `await client.aget_file_content(file_id)` | `await client.a_files.retrieve_content(file_id)` |
| `await client.aget_image(file_id)` | `await client.a_files.retrieve_content(file_id)` |

`client.files.retrieve_image(file_id)` / `client.a_files.retrieve_image(file_id)` оставить как compatibility resource aliases, если они уже есть после PR `#110`. Они должны делегировать в `retrieve_content`. Предпочтительно пометить их deprecated warning-ом как старое image-only имя; если это ломает существующий тест PR `#110`, обновить тесты и migration docs в том же срезе 6.

Существующий file CRUD из PR `#110` не переделывать:

```python
client.files.upload(...)
client.files.retrieve(...)
client.files.list()
client.files.delete(...)
await client.a_files.upload(...)
await client.a_files.retrieve(...)
await client.a_files.list()
await client.a_files.delete(...)
```

### Function validation

| Legacy/root path | Canonical resource path |
|---|---|
| `client.validate_function(function)` | `client.functions.validate(function)` |
| `await client.avalidate_function(function)` | `await client.a_functions.validate(function)` |

`client.functions.convert_openapi(...)` из PR `#110` не переименовывать и не переписывать.

## Source snapshot из `feature/v2_completions`

Проверить эти файлы перед переносом:

```text
src/gigachat/api/batches.py
src/gigachat/models/batches.py
src/gigachat/api/files.py
src/gigachat/models/files.py
src/gigachat/api/tools.py
src/gigachat/models/tools.py
src/gigachat/client.py
tests/constants.py
tests/data/batch.json
tests/data/batches.json
tests/unit/gigachat/api/test_batches.py
tests/unit/gigachat/test_client_batches.py
tests/unit/gigachat/api/test_files.py
tests/unit/gigachat/test_client_files.py
tests/unit/gigachat/api/test_tools.py
tests/unit/gigachat/test_client_functions.py
examples/example_batching.ipynb
```

Не копировать `client.py` целиком из `feature/v2_completions`: там root API, а цель этого плана — resource API.

---

# Срезы и commit-план

## Срез 1 — add follow-up plan/progress docs

**Commit:** `docs(resources): add batches files resource api plan`

**Задача:** добавить plan/progress docs для этого follow-up.

**Файлы:**

```text
docs/internal/RESOURCE_API_BATCHES_FILES_PLAN.md
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

**Что сделать:**

- Добавить этот план в `RESOURCE_API_BATCHES_FILES_PLAN.md`.
- Добавить progress template в `RESOURCE_API_BATCHES_FILES_PROGRESS.md`.
- Отметить срез 1 как `[done]`.
- Добавить запись в журнал progress.

**Тесты:**

```bash
git diff --check
```

**Не делать:**

- Не менять Python-код.
- Не переносить `batches`.
- Не начинать срез 2.

---

## Срез 2 — add low-level batches API and models

**Commit:** `feat(batches): add low-level batch api`

**Задача:** перенести transport-level batches implementation и typed models без resource/client namespace.

**Файлы:**

```text
src/gigachat/api/__init__.py
src/gigachat/api/batches.py
src/gigachat/models/__init__.py
src/gigachat/models/batches.py
src/gigachat/__init__.py
tests/constants.py
tests/data/batch.json
tests/data/batches.json
tests/unit/gigachat/api/test_batches.py
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

**Что сделать:**

- Добавить `BatchMethod`, `BatchStatus`, `BatchRequestCounts`, `Batch`, `Batches`.
- Добавить low-level helpers:
  - `create_batch_sync(...)`
  - `create_batch_async(...)`
  - `get_batches_sync(...)`
  - `get_batches_async(...)`
- Сохранить wire contract:
  - `POST /batches`
  - `Content-Type: application/octet-stream`
  - query param `method=chat_completions|embedder`
  - `GET /batches`
  - optional query param `batch_id`
- Сохранить `_get_batch_content(file)` для `bytes`, `str`, file-like object.
- Сохранить `_parse_batches_payload(...)`: list -> `{"batches": list}`, single object with `id` -> `{"batches": [payload]}`.
- Экспортировать модели так же, как остальные public models.
- Добавить фикстуры `batch.json` и `batches.json`.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/api/test_batches.py -q
uv run ruff check src/gigachat/api/batches.py src/gigachat/models/batches.py tests/unit/gigachat/api/test_batches.py
git diff --check
```

**Не делать:**

- Не добавлять `client.batches`.
- Не добавлять root methods `create_batch/get_batches`.
- Не обновлять docs/examples.
- Не трогать files или functions.

---

## Срез 3 — add batches resource namespace and deprecated root shims

**Commit:** `feat(resources): add batches resource`

**Задача:** добавить canonical resource API для batches и deprecated root shims.

**Файлы:**

```text
src/gigachat/resources/__init__.py
src/gigachat/resources/batches.py
src/gigachat/client.py
tests/unit/gigachat/test_client_batches.py
tests/unit/gigachat/test_client_lifecycle.py
tests/unit/gigachat/test_client_resource_shims.py
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

**Что сделать:**

- Добавить `BatchesSyncResource`:
  - `create(file, method) -> Batch`
  - `list() -> Batches`
  - `retrieve(batch_id: str) -> Batches`
- Добавить `BatchesAsyncResource`:
  - `create(...)`
  - `list()`
  - `retrieve(batch_id)`
- В `GigaChatSyncClient` добавить `@cached_property def batches(...)`.
- В `GigaChatAsyncClient` добавить `@cached_property def a_batches(...)`.
- Добавить deprecated root shims без auth/retry decorators:
  - `client.create_batch(file, method)` -> warn + `client.batches.create(...)`
  - `client.get_batches(batch_id=None)` -> warn + `client.batches.list()` или `client.batches.retrieve(batch_id)`
  - `client.acreate_batch(...)` -> warn + `client.a_batches.create(...)`
  - `client.aget_batches(batch_id=None)` -> warn + `client.a_batches.list()` или `client.a_batches.retrieve(batch_id)`
- Warning должен указывать canonical resource path.
- Resource methods должны иметь auth/retry decorators и не должны warning-ить.
- Не делать double auth/retry wrapping: root shims только делегируют в resource.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_batches.py -q
uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q
uv run pytest tests/unit/gigachat/test_client_resource_shims.py -q
uv run ruff check src/gigachat/resources/batches.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_batches.py
git diff --check
```

**Не делать:**

- Не обновлять notebooks/docs.
- Не менять low-level `api/batches.py`, кроме fallout, обнаруженного тестами текущего среза.
- Не менять return model `Batches` на `Batch`.

---

## Срез 4 — add batch example/docs on resource paths

**Commit:** `docs(batches): add resource batch example`

**Задача:** перенести batch example из `feature/v2_completions`, но заменить root calls на resource calls.

**Файлы-кандидаты:**

```text
examples/example_batching.ipynb
examples/README.md
README.md
MIGRATION_GUIDE.md
MIGRATION_GUIDE_ru.md
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

**Что сделать:**

- Перенести пример batch flow:
  - прочитать JSONL input;
  - `client.batches.create(data, method="chat_completions")`;
  - `client.batches.retrieve(batch_id)` или `client.batches.list()`;
  - скачать output через `client.files.retrieve_content(output_file_id)` — если срез 6 ещё не сделан, в этом срезе использовать временную ссылку в docs как future path, но не менять Python API.
- Не использовать `client.create_batch(...)` как canonical пример.
- В README/MIGRATION добавить краткий mapping для batches.

**Тесты:**

```bash
git diff --check
uv run ruff check README.md MIGRATION_GUIDE.md MIGRATION_GUIDE_ru.md examples/README.md
```

Если `ruff` не применим к `.md`, записать это в progress и выполнить только `git diff --check`.

**Не делать:**

- Не менять production Python-код.
- Не добавлять file content API в этом срезе.
- Не править unrelated examples.

---

## Срез 5 — add low-level file content API and File model

**Commit:** `feat(files): add low-level file content api`

**Задача:** добрать из `feature/v2_completions` `get_file_content`/`File` на transport/model level.

**Файлы:**

```text
src/gigachat/api/files.py
src/gigachat/models/files.py
src/gigachat/models/__init__.py
src/gigachat/__init__.py
tests/unit/gigachat/api/test_files.py
tests/unit/gigachat/models/test_files.py
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

**Что сделать:**

- Добавить модель `File(APIResponse)` с `content: str`.
- Оставить `Image` как deprecated compatibility model, если она уже есть.
- В `api/files.py` добавить:
  - `_get_file_content_kwargs(file_id, access_token)`
  - `_build_file_content_response(response) -> File`
  - `get_file_content_sync(...) -> File`
  - `get_file_content_async(...) -> File`
- Сохранить wire contract:
  - `GET /files/{file_id}/content`
  - текущий `Accept: application/jpg`, если он уже используется API, но docstring сделать generic: `file content in base64 encoding`.
- `get_image_sync/get_image_async` оставить aliases к `get_file_content_*` с `DeprecationWarning`.
- Убедиться, что file CRUD из PR `#110` не поменялся.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/api/test_files.py -q
uv run pytest tests/unit/gigachat/models/test_files.py -q
uv run ruff check src/gigachat/api/files.py src/gigachat/models/files.py tests/unit/gigachat/api/test_files.py tests/unit/gigachat/models/test_files.py
git diff --check
```

**Не делать:**

- Не добавлять `client.files.retrieve_content`.
- Не менять root `get_image` в client.
- Не менять examples/docs.

---

## Срез 6 — add files.retrieve_content resource path and shims

**Commit:** `feat(resources): add file content resource`

**Задача:** сделать canonical Resource API для получения file content и совместимость со старым image-only API.

**Файлы:**

```text
src/gigachat/resources/files.py
src/gigachat/client.py
tests/unit/gigachat/test_client_files.py
tests/unit/gigachat/test_client_resource_shims.py
tests/unit/gigachat/test_client_lifecycle.py
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

**Что сделать:**

- В `FilesSyncResource` добавить:
  - `retrieve_content(file_id: str) -> File`
  - `retrieve_image(file_id: str) -> File` как deprecated compatibility alias к `retrieve_content`.
- В `FilesAsyncResource` добавить async equivalents.
- В client добавить deprecated root shims:
  - `get_file_content(file_id)` -> `files.retrieve_content(file_id)`
  - `get_image(file_id)` -> `files.retrieve_content(file_id)`
  - `aget_file_content(file_id)` -> `a_files.retrieve_content(file_id)`
  - `aget_image(file_id)` -> `a_files.retrieve_content(file_id)`
- Root shims не должны иметь auth/retry decorators.
- Resource canonical `retrieve_content` не должен warning-ить.
- Compatibility alias `retrieve_image` должен warning-ить, если принято deprecated image-only имя. Если существующие tests PR `#110` ожидали no-warning для `retrieve_image`, обновить их в этом же срезе и явно записать причину в progress.
- Обновить type imports: `File` вместо `Image` там, где теперь generic content.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_files.py -q
uv run pytest tests/unit/gigachat/test_client_resource_shims.py -q
uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q
uv run ruff check src/gigachat/resources/files.py src/gigachat/client.py tests/unit/gigachat/test_client_files.py tests/unit/gigachat/test_client_resource_shims.py
git diff --check
```

**Не делать:**

- Не менять upload/list/retrieve/delete.
- Не менять `api/files.py`, кроме fallout из среза 5.
- Не трогать batches/functions.

---

## Срез 7 — add low-level function validation API and models

**Commit:** `feat(functions): add low-level function validation api`

**Задача:** перенести `/functions/validate` из `feature/v2_completions` на low-level API/model level.

**Файлы:**

```text
src/gigachat/api/tools.py
src/gigachat/models/tools.py
src/gigachat/models/__init__.py
src/gigachat/__init__.py
tests/unit/gigachat/api/test_tools.py
tests/unit/gigachat/models/test_tools.py
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

**Что сделать:**

- Добавить `FunctionValidationIssue`.
- Добавить `FunctionValidationResult`.
- Добавить low-level helpers:
  - `_get_function_validate_kwargs(function, access_token)`
  - `function_validate_sync(...)`
  - `function_validate_async(...)`
- Payload строить через `Function.model_validate(function).model_dump(by_alias=True, exclude_none=True)`.
- Сохранить wire contract:
  - `POST /functions/validate`
  - JSON body function schema.
- Не менять `/functions/convert`.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/api/test_tools.py -q
uv run pytest tests/unit/gigachat/models/test_tools.py -q
uv run ruff check src/gigachat/api/tools.py src/gigachat/models/tools.py tests/unit/gigachat/api/test_tools.py tests/unit/gigachat/models/test_tools.py
git diff --check
```

Если `tests/unit/gigachat/models/test_tools.py` отсутствует, создать минимальный test только для новых validation models.

**Не делать:**

- Не добавлять `client.functions.validate`.
- Не менять chat function-calling models.
- Не трогать `Function` / `FunctionParameters`, кроме import fallout.

---

## Срез 8 — add functions.validate resource path and shims

**Commit:** `feat(resources): add function validation resource`

**Задача:** сделать canonical Resource API для function validation.

**Файлы:**

```text
src/gigachat/resources/functions.py
src/gigachat/client.py
tests/unit/gigachat/test_client_functions.py
tests/unit/gigachat/test_client_resource_shims.py
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

**Что сделать:**

- В `FunctionsSyncResource` добавить `validate(function) -> FunctionValidationResult`.
- В `FunctionsAsyncResource` добавить async `validate(function)`.
- Добавить root deprecated shims:
  - `client.validate_function(function)` -> `client.functions.validate(function)`
  - `await client.avalidate_function(function)` -> `await client.a_functions.validate(function)`
- Shims должны warning-ить с новым resource path.
- Resource methods не warning-ят.
- Не менять `convert_openapi`.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_functions.py -q
uv run pytest tests/unit/gigachat/test_client_resource_shims.py -q
uv run ruff check src/gigachat/resources/functions.py src/gigachat/client.py tests/unit/gigachat/test_client_functions.py tests/unit/gigachat/test_client_resource_shims.py
git diff --check
```

**Не делать:**

- Не менять `api/tools.py`, кроме fallout из среза 7.
- Не обновлять docs/examples.
- Не менять chat tools surface.

---

## Срез 9 — add global resource/shim regression coverage

**Commit:** `test(resources): cover batches files functions shims`

**Задача:** расширить общую regression matrix по canonical resources и deprecated shims.

**Файлы:**

```text
tests/unit/gigachat/test_client_resource_shims.py
tests/unit/gigachat/test_client_lifecycle.py
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

**Что покрыть:**

- `client.batches is client.batches` и `client.a_batches is client.a_batches`.
- `client.files.retrieve_content(...)` no warning.
- `client.files.retrieve_image(...)` compatibility behavior, если alias оставлен.
- `client.functions.validate(...)` no warning.
- Root shims warning-ят:
  - `create_batch`
  - `get_batches`
  - `acreate_batch`
  - `aget_batches`
  - `get_file_content`
  - `aget_file_content`
  - `get_image`
  - `aget_image`
  - `validate_function`
  - `avalidate_function`
- Deprecated shims делегируют в те же low-level APIs, что и resource methods.

**Тесты:**

```bash
uv run pytest tests/unit/gigachat/test_client_resource_shims.py -q
uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q
uv run ruff check tests/unit/gigachat/test_client_resource_shims.py tests/unit/gigachat/test_client_lifecycle.py
git diff --check
```

**Не делать:**

- Не менять production-код, кроме исправления failures, обнаруженных именно этими тестами.
- Не добавлять docs/examples.

---

## Срез 10 — update public docs and migration guides

**Commit:** `docs(resources): document batches files function validation resources`

**Задача:** обновить public docs на canonical Resource API.

**Файлы-кандидаты:**

```text
README.md
MIGRATION_GUIDE.md
MIGRATION_GUIDE_ru.md
examples/README.md
examples/example_batching.ipynb
examples/files/*
docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md
```

**Что сделать:**

- В README показать canonical calls:
  - `client.batches.create(...)`
  - `client.batches.list()` / `client.batches.retrieve(...)`
  - `client.files.retrieve_content(...)`
  - `client.functions.validate(...)`
- В migration guides добавить mapping root -> resource:
  - batches root methods;
  - file content and image aliases;
  - function validation.
- Убедиться, что examples не рекламируют root API как canonical.
- Если `examples/example_batching.ipynb` уже добавлен в срезе 4 с временным text, привести его к полностью рабочему resource flow.

**Паттерны поиска:**

```bash
rg "create_batch|get_batches|acreate_batch|aget_batches|get_file_content|aget_file_content|get_image|aget_image|retrieve_image|validate_function|avalidate_function|function_validate" README.md MIGRATION_GUIDE*.md examples tests
```

Допустимые совпадения:

- migration replacement tables;
- deprecated shim tests;
- progress/plan docs;
- compatibility alias docs.

**Тесты:**

```bash
git diff --check
uv run pytest tests/unit/examples -q
```

Если `tests/unit/examples` отсутствует или не применим, записать это в progress.

**Не делать:**

- Не менять production API.
- Не переписывать chat docs.
- Не менять unrelated examples.

---

## Срез 11 — final audit and cleanup

**Commit:** `chore(resources): finish batches files resource migration`

**Задача:** финальная проверка, что canonical surface — resource API, а root API только compatibility.

**Что проверить:**

```bash
rg "client\.create_batch|client\.get_batches|client\.acreate_batch|client\.aget_batches|client\.get_file_content|client\.aget_file_content|client\.get_image|client\.aget_image|client\.validate_function|client\.avalidate_function" .
```

Допустимые совпадения:

- migration guides;
- deprecated shim tests;
- progress/plan docs;
- warning strings.

**Финальные команды:**

```bash
uv run ruff check .
uv run pytest
make mypy
git diff --check
```

**Что сделать в progress:**

- Записать полный список команд и результаты.
- Если команда не может быть запущена локально, записать точную причину.
- Если команда не прошла, не делать final commit до исправления.

**Не делать:**

- Не добавлять новые features.
- Не менять chat v1/v2.
- Не удалять deprecated shims.
- Не делать version bump.

---

# Definition of Done всего follow-up

Работа считается завершённой, если:

1. `batches` доступны через `client.batches.*` и `client.a_batches.*`.
2. Старые root batch methods работают как deprecated shims.
3. File content доступен через `client.files.retrieve_content(...)` и `client.a_files.retrieve_content(...)`.
4. `get_image` / `aget_image` и, если оставлен, `retrieve_image` работают как compatibility aliases.
5. `/functions/validate` доступен через `client.functions.validate(...)` и `client.a_functions.validate(...)`.
6. Старые root validation methods работают как deprecated shims.
7. Все canonical resource methods покрыты тестами на отсутствие warnings.
8. Все deprecated shims покрыты тестами на `DeprecationWarning`.
9. Все resource namespaces на клиенте ленивые и кешируются через `cached_property`.
10. README/examples показывают resource API как canonical.
11. Migration guides содержат mapping старых root methods на новые resource paths.
12. `uv run ruff check .`, `uv run pytest`, `make mypy`, `git diff --check` проходят или в progress зафиксирована честная причина, почему команда не запускалась.
13. `docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md` содержит журнал каждого среза и commit message/hash.

## Формат ответа после каждого среза

```md
## Прогресс

Срез: N — <название>
Статус: done
Commit: <hash> `<message>`

Что сделано:
- ...

Изменённые файлы:
- ...

Тесты:
- `<command>` — passed

Замечания:
- ...

Что осталось:
- следующий срез: N+1 — <название>
```

Не писать «заодно сделал следующий срез». Если следующий срез тоже нужен, он делается отдельным заходом.
