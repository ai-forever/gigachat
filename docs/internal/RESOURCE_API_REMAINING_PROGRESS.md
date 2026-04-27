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
