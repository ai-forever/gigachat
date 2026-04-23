# GPT-5.4 Codex playbook для `feature/resource_api`

## Цель
Сделать новый основной chat surface поверх нового `chat/completions` контракта, не ломая явный legacy-слой.

Целевой публичный API:

```python
client.chat.create(...)
client.chat.stream(...)
client.chat.parse(...)

client.chat.legacy.create(...)
client.chat.legacy.stream(...)
client.chat.legacy.parse(...)

await client.achat.create(...)
client.achat.stream(...)
await client.achat.parse(...)

await client.achat.legacy.create(...)
client.achat.legacy.stream(...)
await client.achat.legacy.parse(...)
```

## Жесткие правила
1. За один заход брать только **одну** задачу.
2. Один срез = один атомарный результат = один commit.
3. После каждого среза: прогнать релевантные тесты, закоммитить, записать прогресс, остановиться.
4. Нельзя использовать имена файлов и классов с суффиксами `v2` / `V2`.
5. Старый стек должен стать `legacy`, а не новый стек должен стать `v2`.
6. `client.chat` и `client.achat` должны оставаться resource-объектами на `cached_property`.
7. Deprecated root-shims должны продолжать вести в legacy-поведение, а не в новый основной API.
8. Нельзя смешивать в одном commit несколько смыслов: rename + feature + docs = запрещено.
9. Нельзя делать opportunistic cleanup вне текущего среза.
10. Если уперся в blocker, остановись, опиши blocker и **не** начинай следующий срез.
11. Если сомневаешься, дроби задачу еще сильнее.

## Правило именования
### Legacy-стек
Используй явные `legacy`-имена.

Предпочтительная структура:
- `src/gigachat/models/legacy_chat.py`
- `src/gigachat/api/legacy_chat.py`

Предпочтительные имена классов:
- `LegacyChat`
- `LegacyChatCompletion`
- `LegacyChatCompletionChunk`
- `LegacyMessage`
- `LegacyMessageChunk`
- `LegacyChoice`
- `LegacyChoiceChunk`
- `LegacyUsage`
- `LegacyStorage`
- `LegacyMessageRole`

### Новый основной стек
Используй смысловые имена без версии.

Предпочтительная структура:
- `src/gigachat/models/chat_completions.py`
- `src/gigachat/api/chat_completions.py`

Предпочтительные имена классов:
- `ChatCompletionRequest`
- `ChatCompletionResponse`
- `ChatCompletionChunk`
- `ChatMessage`
- `ChatContentPart`
- `ChatUsage`
- `ChatToolConfig`
- `ChatModelOptions`
- `ChatFilterConfig`

### Совместимость
- `src/gigachat/models/chat.py` должен остаться compatibility-layer для старых импортов.
- Старые публичные импорты (`Chat`, `ChatCompletion`, `ChatCompletionChunk` и т.д.) пока должны оставаться рабочими и указывать на legacy-алиасы.
- Не переворачивай старые публичные имена на новый контракт в этой задаче.

## Что уже есть в ветке и что нельзя ломать
- `client.chat` / `client.achat` уже существуют как namespace/resource-объекты.
- `.legacy` уже оформлен как явная ветка API.
- root compatibility shims уже deprecated и должны оставаться legacy-шинами.
- текущие `api/chat.py` и `models/chat.py` описывают старый wire-format, а не новый основной контракт.

## Что важно про новый контракт
Новый request/response materially отличается от legacy, поэтому его нельзя натягивать на старые модели.

### В request есть поля уровня root/message, которых нет в legacy
- `messages[]`
- `assistant_id`
- `tools_state_id`
- multipart `content[]`
- `model_options`
- `reasoning`
- `response_format`
- `filter_config`
- `storage.thread_id`
- `ranker_options`
- `tool_config`
- `tools`
- `user_info`

### В response есть поля, которых нет в legacy
- top-level `messages[]`
- `created_at`
- `thread_id`
- `tool_execution`
- `logprobs`
- `usage.input_tokens`
- `usage.output_tokens`
- `usage.total_tokens`
- `usage.input_tokens_details.cached_tokens`
- `additional_data.execution_steps`

## Неоднозначности спецификации
Спецификация не идеальна. Делай новые модели терпимыми к росту и неоднозначностям.

Обязательные принципы:
- разрешай `extra="allow"` там, где wire-format может расти;
- принимай `content` и как строку, и как массив частей, если это помогает совместимости со спецификацией;
- не делай стриминговые chunk-модели слишком строгими;
- если `response_format.schema` приходит неидеально типизированным, поддержи практичный вариант;
- не выдумывай жесткие ограничения там, где их нет в контракте.

## Обязательный протокол прогресса
Каждый ответ Codex **обязан** начинаться с блока:

```md
Progress: S2/11 — done
Current slice: Вынести текущий transport в explicit legacy
Done in this turn:
- moved legacy chat transport into `src/gigachat/api/legacy_chat.py`
- kept `src/gigachat/api/chat.py` as a compatibility shim over the legacy transport
- rewired sync and async legacy client internals to use the explicit legacy transport module
- added sync and async routing tests for explicit legacy transport usage
Tests:
- `uv run pytest tests/unit/gigachat/api/test_chat.py tests/unit/gigachat/test_client_chat.py tests/unit/gigachat/test_client_chat_parse.py`
- `uv run ruff check src/gigachat/api/legacy_chat.py src/gigachat/api/chat.py src/gigachat/api/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_chat.py`
Commit:
- refactor(chat): move legacy transport under explicit legacy module
Next slice (do not start now):
- S3 — Добавить типизированные primary-модели
Blockers:
- none
```

И после каждого завершенного среза Codex обязан обновить секцию `## Progress log` внизу этого файла.

## Definition of done для каждого среза
Срез считается завершенным только если одновременно выполнены все пункты:
- сделана ровно одна задача;
- изменены только файлы, нужные для этой задачи;
- прогнаны релевантные тесты;
- создан ровно один commit;
- записан прогресс;
- работа остановлена после commit;
- следующий срез **не** начат.

## Правила для commit
- один commit на один срез;
- commit message должен отражать один результат;
- предпочтительные префиксы: `refactor(chat)`, `feat(chat)`, `test(chat)`, `docs(chat)`;
- запрещены commit messages вида `wip`, `tmp`, `misc`, `small fixes`, `cleanup`.

## Порядок срезов
Ниже — порядок, который нужно соблюдать. Следующий срез можно брать только после того, как предыдущий завершен, закоммичен и отмечен в прогрессе.

### S1 — Вынести текущие chat-модели в explicit legacy
**Результат:**
- текущие модели из `models/chat.py` переезжают в `models/legacy_chat.py`;
- ключевые классы получают `Legacy...`-имена;
- `models/chat.py` становится backward-compatible shim-слоем;
- публичные импорты из `gigachat.models` остаются рабочими.

**Файлы:**
- `src/gigachat/models/legacy_chat.py`
- `src/gigachat/models/chat.py`
- `src/gigachat/models/__init__.py`
- минимальные import-fixups

**Тесты:**
- старые импорты продолжают работать;
- legacy-сериализация и legacy-десериализация не меняются.

**Commit:**
- `refactor(chat): extract legacy chat models with compat aliases`

**Важно:**
- в этом срезе нельзя добавлять новые primary-модели;
- в этом срезе нельзя менять поведение клиента.

### S2 — Вынести текущий transport в explicit legacy
**Результат:**
- старый transport переезжает в `api/legacy_chat.py`;
- legacy-resource и client internals начинают использовать explicit legacy transport;
- поведение legacy endpoint не меняется.

**Файлы:**
- `src/gigachat/api/legacy_chat.py`
- import-fixups в client/resources/tests
- временный tiny-shim только если без него нельзя сохранить совместимость

**Тесты:**
- `client.chat.legacy.create(...)` остается на legacy route;
- `client.chat.legacy.stream(...)` остается на legacy stream path.

**Commit:**
- `refactor(chat): move legacy transport under explicit legacy module`

### S3 — Добавить типизированные primary-модели
**Результат:**
- появляется новый набор typed-моделей для нового контракта;
- client wiring еще не трогаем.

**Файлы:**
- `src/gigachat/models/chat_completions.py`
- при необходимости минимальные экспорты в `src/gigachat/models/__init__.py`

**Минимальный набор моделей:**
- request root;
- response root;
- stream chunk;
- message;
- content parts;
- files;
- `tool_config` / tool specs / function specs;
- `reasoning` / `model_options` / `filter_config` / `ranker_options` / `storage` / `usage` / `logprobs` / `tool_execution`.

**Тесты:**
- request-пример парсится и сериализуется;
- response-пример парсится;
- неоднозначный `content` корректно нормализуется.

**Commit:**
- `feat(chat): add primary chat completion models`

### S4 — Подключить sync primary create
**Результат:**
- появляется sync non-stream path для нового основного API;
- `client.chat.create(...)` идет в новый endpoint;
- `client.chat.legacy.create(...)` остается на старом endpoint;
- stream и parse в этом срезе не трогаем.

**Файлы:**
- `src/gigachat/api/chat_completions.py`
- `src/gigachat/resources/chat.py`
- `src/gigachat/client.py`
- `src/gigachat/context.py`, если нужен отдельный URL/context var для нового endpoint

**Правила:**
- не использовать legacy `chat_url_cvar`, если это свяжет v1 и новый primary route;
- принимать `str | dict | ChatCompletionRequest` и нормализовывать вход.

**Тесты:**
- `client.chat.create(...)` идет в новый route;
- `client.chat.legacy.create(...)` идет в legacy route;
- `client.chat is client.chat`.

**Commit:**
- `feat(chat): wire sync primary create`

### S5 — Подключить sync primary stream
**Результат:**
- `client.chat.stream(...)` работает для нового основного API;
- legacy stream остается без изменений.

**Файлы:**
- только stream-related код в transport/resource/client area

**Тесты:**
- `client.chat.stream(...)` идет в primary stream route;
- stream chunks парсятся новой chunk-model;
- `client.chat.legacy.stream(...)` остается на legacy model.

**Commit:**
- `feat(chat): add sync primary stream`

### S6 — Подключить sync primary parse
**Результат:**
- `client.chat.parse(...)` работает для нового основного API.

**Требования:**
- принимать Pydantic-модель в `response_format`;
- собирать JSON Schema request payload;
- извлекать JSON из assistant text content в новом response shape;
- явно обрабатывать strict/non-strict path;
- async parse в этом срезе не трогать.

**Тесты:**
- happy path structured parse;
- invalid JSON;
- schema validation error;
- обработка finish/length path, если он поддержан новым wire-format.

**Commit:**
- `feat(chat): add sync primary parse`

### S7 — Подключить async primary create
**Результат:**
- `await client.achat.create(...)` работает для нового основного API.

**Тесты:**
- async primary create route;
- `await client.achat.legacy.create(...)` остается legacy.

**Commit:**
- `feat(chat): wire async primary create`

### S8 — Подключить async primary stream
**Результат:**
- `client.achat.stream(...)` работает для нового основного API.

**Тесты:**
- async primary stream route;
- async legacy stream остается без изменений.

**Commit:**
- `feat(chat): add async primary stream`

### S9 — Подключить async primary parse
**Результат:**
- `await client.achat.parse(...)` работает для нового основного API.

**Тесты:**
- async structured parse;
- async validation error path.

**Commit:**
- `feat(chat): add async primary parse`

### S10 — Закрыть regression matrix для primary vs legacy
**Результат:**
- появляется явная матрица тестов на маршрутизацию, cached_property и compatibility.

**Обязательно покрыть:**
- `client.chat is client.chat`;
- `client.chat.legacy is client.chat.legacy`;
- то же для async;
- deprecated root shims по-прежнему warning + legacy behavior;
- старые model imports по-прежнему резолвятся;
- primary и legacy случайно не используют один и тот же response-model contract.

**Commit:**
- `test(chat): cover primary and legacy routing matrix`

### S11 — Обновить README и примеры
**Результат:**
- README и examples показывают primary surface первым;
- legacy остается явно описанным;
- нигде не появляется `v2`-нейминг;
- документировано, что старые `gigachat.models.Chat*` импорты пока являются legacy-compat alias during migration.

**Commit:**
- `docs(chat): document primary and legacy chat surfaces`

## Что делать нельзя вне активного среза
- рефакторить другие resources;
- переименовывать assistants/threads;
- переписывать auth/retry;
- массово форматировать нерелевантные файлы;
- переносить unrelated imports просто "по пути";
- менять публичную семантику legacy;
- начинать docs до завершения кодовых срезов.

## Stop conditions
Остановиться сразу после одного из событий:
- текущий срез завершен, протестирован, закоммичен и прогресс записан;
- найден blocker, он записан, следующий срез не начат.

## Progress log
- [x] S1 — Вынести текущие chat-модели в explicit legacy
- [x] S2 — Вынести текущий transport в explicit legacy
- [ ] S3 — Добавить типизированные primary-модели
- [ ] S4 — Подключить sync primary create
- [ ] S5 — Подключить sync primary stream
- [ ] S6 — Подключить sync primary parse
- [ ] S7 — Подключить async primary create
- [ ] S8 — Подключить async primary stream
- [ ] S9 — Подключить async primary parse
- [ ] S10 — Закрыть regression matrix для primary vs legacy
- [ ] S11 — Обновить README и примеры

## Execution log
| Step | Slice | Status | Commit | Tests | Notes |
|---|---|---|---|---|---|
| 1 | S1 | done | refactor(chat): extract legacy chat models with compat aliases | `uv run pytest tests/unit/gigachat/models/test_chat.py tests/unit/gigachat/models/test_response_format.py tests/unit/gigachat/api/test_chat.py tests/unit/gigachat/test_client_chat.py tests/unit/gigachat/test_client_chat_parse.py`; `uv run ruff check src/gigachat/models/legacy_chat.py src/gigachat/models/chat.py src/gigachat/models/__init__.py tests/unit/gigachat/models/test_chat.py` | Extracted legacy chat models to `models/legacy_chat.py`, kept `models/chat.py` as compatibility shim, and exposed explicit `Legacy...` names via `gigachat.models`. |
| 2 | S2 | done | refactor(chat): move legacy transport under explicit legacy module | `uv run pytest tests/unit/gigachat/api/test_chat.py tests/unit/gigachat/test_client_chat.py tests/unit/gigachat/test_client_chat_parse.py`; `uv run ruff check src/gigachat/api/legacy_chat.py src/gigachat/api/chat.py src/gigachat/api/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_chat.py` | Moved legacy transport into `api/legacy_chat.py`, kept `api/chat.py` as a compatibility shim, rewired legacy client internals to the explicit module, and added sync/async routing checks for `client.chat.legacy` and `client.achat.legacy`. |
