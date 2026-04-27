# Resource API Batches/Files Progress

План: docs/internal/RESOURCE_API_BATCHES_FILES_PLAN.md

## Правила

- Один заход = один срез.
- Один срез = один commit.
- Перед commit обновлять этот файл.
- Нельзя начинать следующий срез в том же заходе.

## Срезы

1. [done] Add follow-up plan/progress docs
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
- 2026-04-27: завершён срез 1.
  - Что сделано: добавлены follow-up plan/progress docs.
  - Изменённые файлы: docs/internal/RESOURCE_API_BATCHES_FILES_PLAN.md, docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md.
  - Тесты: git diff --check.
  - Commit: docs(resources): add batches files resource api plan
  - Замечания: Python-код не менялся.
