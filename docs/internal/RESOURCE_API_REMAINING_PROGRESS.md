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
