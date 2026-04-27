# Resource API Remaining Progress

План: docs/internal/RESOURCE_API_REMAINING_PLAN.md

## Правила

- Один заход = один срез.
- Один срез = один commit.
- Перед commit обновлять этот файл.
- Нельзя начинать следующий срез в том же заходе.

## Срезы

1. [done] Restore plan/progress docs
2. [done] Add shared resource deprecation helper
3. [done] Normalize assistants resource module
4. [done] Normalize threads resource module
5. [done] Add models resource
6. [done] Add embeddings resource
7. [done] Add files resource
8. [done] Add tokens resource
9. [done] Add balance resource
10. [done] Add functions resource
11. [done] Add ai_check resource
12. [done] Update docs/examples for non-chat resources
13. [done] Add global resource/shim regression tests
14. [done] Final audit and cleanup

## Журнал

- 2026-04-27: план создан.
- 2026-04-27: завершён срез 1.
  - Что сделано: восстановлены plan/progress docs для оставшихся Resource API работ.
  - Изменённые файлы: `docs/internal/RESOURCE_API_REMAINING_PLAN.md`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `git diff --check`.
  - Commit: `docs(resources): add remaining resource api plan`.
  - Замечания: Python-код не менялся; следующие срезы не начинались.
- 2026-04-27: завершён срез 2.
  - Что сделано: добавлен общий helper `warn_deprecated_resource_api()` для deprecated root shims non-chat Resource API.
  - Изменённые файлы: `src/gigachat/resources/_utils.py`, `src/gigachat/resources/__init__.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_chat.py -q`, `git diff --check`.
  - Commit: `refactor(resources): add deprecated resource shim helper`.
  - Замечания: новые resources не добавлялись; chat shims не переподключались.
- 2026-04-27: завершён срез 3.
  - Что сделано: `AssistantsSyncClient` и `AssistantsAsyncClient` перенесены в `gigachat.resources.assistants`; старый `gigachat.assistants` оставлен как compatibility module.
  - Изменённые файлы: `src/gigachat/assistants.py`, `src/gigachat/resources/assistants.py`, `src/gigachat/resources/__init__.py`, `src/gigachat/client.py`, `tests/unit/gigachat/test_client_assistants.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_assistants.py -q`, `uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q`, `uv run ruff check src/gigachat/assistants.py src/gigachat/resources/assistants.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_assistants.py`, `git diff --check`.
  - Commit: `refactor(resources): move assistants resource into resources package`.
  - Замечания: public paths `client.assistants.*` и `client.a_assistants.*` не менялись; threads не трогались.
- 2026-04-27: завершён срез 4.
  - Что сделано: `ThreadsSyncClient` и `ThreadsAsyncClient` перенесены в `gigachat.resources.threads`; старый `gigachat.threads` оставлен как compatibility module.
  - Изменённые файлы: `src/gigachat/threads.py`, `src/gigachat/resources/threads.py`, `src/gigachat/resources/__init__.py`, `src/gigachat/client.py`, `tests/unit/gigachat/test_client_threads.py`, `tests/unit/gigachat/test_client_lifecycle.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_threads.py -q`, `uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q`, `uv run ruff check src/gigachat/threads.py src/gigachat/resources/threads.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_threads.py tests/unit/gigachat/test_client_lifecycle.py`, `git diff --check`.
  - Commit: `refactor(resources): move threads resource into resources package`.
  - Замечания: public paths `client.threads.*` и `client.a_threads.*` не менялись; assistants и chat не трогались.
- 2026-04-27: завершён срез 5.
  - Что сделано: добавлен `models` resource namespace с `list()`/`retrieve()` для sync и async клиентов; root methods `get_models`/`get_model` и `aget_models`/`aget_model` переведены в deprecated shims.
  - Изменённые файлы: `src/gigachat/resources/models.py`, `src/gigachat/resources/__init__.py`, `src/gigachat/client.py`, `tests/unit/gigachat/test_client_models.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_models.py -q`, `uv run pytest tests/unit/gigachat/api/test_models.py -q`, `uv run ruff check src/gigachat/resources/models.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_models.py`, `git diff --check`.
  - Commit: `feat(resources): add models resource`.
  - Замечания: transport/API layer не менялся; новые resource methods не предупреждают, deprecated shims предупреждают через общий helper.
- 2026-04-27: завершён срез 6.
  - Что сделано: добавлен `embeddings` resource namespace с `create()` для sync и async клиентов; `client.embeddings(...)` оставлен callable deprecated shim, `client.aembeddings(...)` переведён в deprecated root shim.
  - Изменённые файлы: `src/gigachat/resources/embeddings.py`, `src/gigachat/resources/__init__.py`, `src/gigachat/client.py`, `tests/unit/gigachat/test_client_embeddings.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_embeddings.py -q`, `uv run pytest tests/unit/gigachat/api/test_embeddings.py -q`, `uv run ruff check src/gigachat/resources/embeddings.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_embeddings.py`, `git diff --check`.
  - Commit: `feat(resources): add embeddings resource`.
  - Замечания: default model сохранён как `"Embeddings"`; transport/API layer не менялся.
- 2026-04-27: завершён срез 7.
  - Что сделано: добавлен `files` resource namespace с upload/retrieve/list/delete/retrieve_image для sync и async клиентов; root methods переведены в deprecated shims.
  - Изменённые файлы: `src/gigachat/resources/files.py`, `src/gigachat/resources/__init__.py`, `src/gigachat/client.py`, `tests/unit/gigachat/test_client_files.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_files.py -q`, `uv run pytest tests/unit/gigachat/api/test_files.py -q`, `uv run ruff check src/gigachat/resources/files.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_files.py`, `git diff --check`.
  - Commit: `feat(resources): add files resource`.
  - Замечания: `purpose: Literal["general", "assistant"] = "general"` сохранён; assistants file APIs и upload transport не менялись.
- 2026-04-27: завершён срез 8.
  - Что сделано: добавлен `tokens` resource namespace с `count()` для sync и async клиентов; root methods `tokens_count`/`atokens_count` переведены в deprecated shims.
  - Изменённые файлы: `src/gigachat/resources/tokens.py`, `src/gigachat/resources/__init__.py`, `src/gigachat/client.py`, `tests/unit/gigachat/test_client_tokens.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_tokens.py -q`, `uv run pytest tests/unit/gigachat/api/test_tools.py -q`, `uv run ruff check src/gigachat/resources/tokens.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_tokens.py`, `git diff --check`.
  - Commit: `feat(resources): add tokens resource`.
  - Замечания: fallback модели сохранён как `self._settings.model or GIGACHAT_MODEL`; balance/functions/ai_check не трогались.
- 2026-04-27: завершён срез 9.
  - Что сделано: добавлен `balance` resource namespace с `get()` для sync и async клиентов; root methods `get_balance`/`aget_balance` переведены в deprecated shims.
  - Изменённые файлы: `src/gigachat/resources/balance.py`, `src/gigachat/resources/__init__.py`, `src/gigachat/client.py`, `tests/unit/gigachat/test_client_balance.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_balance.py -q`, `uv run pytest tests/unit/gigachat/api/test_tools.py -q`, `uv run ruff check src/gigachat/resources/balance.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_balance.py`, `git diff --check`.
  - Commit: `feat(resources): add balance resource`.
  - Замечания: 403/ошибки остаются на transport/API layer; token counting и function convert не трогались.
- 2026-04-27: завершён срез 10.
  - Что сделано: добавлен `functions` resource namespace с `convert_openapi()` для sync и async клиентов; root methods `openapi_function_convert`/`aopenapi_function_convert` переведены в deprecated shims.
  - Изменённые файлы: `src/gigachat/resources/functions.py`, `src/gigachat/resources/__init__.py`, `src/gigachat/client.py`, `tests/unit/gigachat/test_client_functions.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_functions.py -q`, `uv run pytest tests/unit/gigachat/api/test_tools.py -q`, `uv run ruff check src/gigachat/resources/functions.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_functions.py`, `git diff --check`.
  - Commit: `feat(resources): add functions resource`.
  - Замечания: chat function calling models и `Function`/`FunctionParameters` не менялись.
- 2026-04-27: завершён срез 11.
  - Что сделано: добавлен `ai_check` resource namespace с `check()` для sync и async клиентов; root methods `check_ai`/`acheck_ai` переведены в deprecated shims.
  - Изменённые файлы: `src/gigachat/resources/ai_check.py`, `src/gigachat/resources/__init__.py`, `src/gigachat/client.py`, `tests/unit/gigachat/test_client_ai_check.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_ai_check.py -q`, `uv run pytest tests/unit/gigachat/api/test_tools.py -q`, `uv run pytest tests/unit/gigachat/test_client_tools.py -q`, `uv run ruff check src/gigachat/resources/ai_check.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_ai_check.py`, `git diff --check`.
  - Commit: `feat(resources): add ai check resource`.
  - Замечания: examples/docs и unrelated tools endpoints не менялись; `test_client_tools.py` проходит с ожидаемыми `DeprecationWarning` для deprecated root paths.
- 2026-04-27: завершён срез 12.
  - Что сделано: публичные README, migration guides и examples обновлены на non-chat resource paths; deprecated root calls описаны как compatibility shims.
  - Изменённые файлы: `README.md`, `MIGRATION_GUIDE.md`, `MIGRATION_GUIDE_ru.md`, `examples/README.md`, `examples/files/file_input.py`, `examples/example_ai_check.ipynb`, `examples/vision/example_vision.ipynb`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/examples -q`, `git diff --check`.
  - Commit: `docs(resources): document non-chat resource api`.
  - Замечания: API-код не менялся; старые root calls остались только в migration replacement tables.
- 2026-04-27: завершён срез 13.
  - Что сделано: добавлена общая sync/async regression matrix для non-chat resource paths и deprecated root shims; lifecycle-тесты расширены на кэширование всех non-chat namespaces.
  - Изменённые файлы: `tests/unit/gigachat/test_client_resource_shims.py`, `tests/unit/gigachat/test_client_lifecycle.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `uv run pytest tests/unit/gigachat/test_client_resource_shims.py -q`, `uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q`, `uv run ruff check tests/unit/gigachat/test_client_resource_shims.py tests/unit/gigachat/test_client_lifecycle.py`, `git diff --check`.
  - Commit: `test(resources): cover non-chat resource shims`.
  - Замечания: production-код не менялся; untracked локальные файлы `api.yml`, `request_v2.pdf`, `response_v2.pdf` не трогались.
- 2026-04-27: завершён срез 14.
  - Что сделано: проведён финальный аудит deprecated non-chat root paths; integration VCR тесты для models/embeddings/tokens переведены на canonical resource paths; исправлена типизация тестов, чтобы полный `make mypy` проходил.
  - Изменённые файлы: `tests/integration/test_embeddings_vcr.py`, `tests/integration/test_models_vcr.py`, `tests/integration/test_tokens_vcr.py`, `tests/unit/gigachat/models/test_chat.py`, `tests/unit/gigachat/test_client_chat.py`, `tests/unit/gigachat/test_client_resource_shims.py`, `tests/unit/gigachat/test_exceptions.py`, `docs/internal/RESOURCE_API_REMAINING_PROGRESS.md`.
  - Тесты: `rg "client\\.get_models|client\\.get_model|client\\.embeddings\\(|client\\.aembeddings\\(|client\\.upload_file|client\\.get_file|client\\.get_files|client\\.delete_file|client\\.get_image|client\\.tokens_count|client\\.get_balance|client\\.openapi_function_convert|client\\.check_ai|client\\.aget_models|client\\.aget_model|client\\.aupload_file|client\\.aget_file|client\\.aget_files|client\\.adelete_file|client\\.aget_image|client\\.atokens_count|client\\.aget_balance|client\\.aopenapi_function_convert|client\\.acheck_ai" .`, `uv run ruff check .`, `uv run pytest`, `make mypy`, `git diff --check`.
  - Commit: `chore(resources): finish non-chat resource api migration`.
  - Замечания: `make mypy` потребовал запуск вне sandbox из-за доступа `uv` к `~/.cache/uv`; финальный запуск прошёл. Оставшиеся audit matches находятся в migration/internal docs, warning strings и deprecated shim tests; локальный untracked `api.yml` также содержит старые примеры, но не входит в git changes и не трогался.
