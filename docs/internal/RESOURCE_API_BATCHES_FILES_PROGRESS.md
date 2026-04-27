# Resource API Batches/Files Progress

План: docs/internal/RESOURCE_API_BATCHES_FILES_PLAN.md

## Правила

- Один заход = один срез.
- Один срез = один commit.
- Перед commit обновлять этот файл.
- Нельзя начинать следующий срез в том же заходе.

## Срезы

1. [done] Add follow-up plan/progress docs
2. [done] Add low-level batches API and models
3. [done] Add batches resource namespace and deprecated root shims
4. [done] Add batch example/docs on resource paths
5. [done] Add low-level file content API and File model
6. [done] Add files.retrieve_content resource path and shims
7. [done] Add low-level function validation API and models
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
- 2026-04-27: завершён срез 2.
  - Что сделано: добавлены low-level batches API helpers, модели, фикстуры и unit-тесты.
  - Изменённые файлы: src/gigachat/api/__init__.py, src/gigachat/api/batches.py, src/gigachat/models/__init__.py, src/gigachat/models/batches.py, src/gigachat/__init__.py, tests/constants.py, tests/data/batch.json, tests/data/batches.json, tests/unit/gigachat/api/test_batches.py, docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md.
  - Тесты: uv run pytest tests/unit/gigachat/api/test_batches.py -q; uv run ruff check src/gigachat/api/batches.py src/gigachat/models/batches.py tests/unit/gigachat/api/test_batches.py; git diff --check.
  - Commit: feat(batches): add low-level batch api
  - Замечания: resource namespace и root shims не добавлялись.
- 2026-04-27: завершён срез 3.
  - Что сделано: добавлены sync/async batches resource namespace, cached properties и deprecated root shims.
  - Изменённые файлы: src/gigachat/resources/__init__.py, src/gigachat/resources/batches.py, src/gigachat/client.py, tests/unit/gigachat/test_client_batches.py, tests/unit/gigachat/test_client_lifecycle.py, tests/unit/gigachat/test_client_resource_shims.py, docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md.
  - Тесты: uv run pytest tests/unit/gigachat/test_client_batches.py -q; uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q; uv run pytest tests/unit/gigachat/test_client_resource_shims.py -q; uv run ruff check src/gigachat/resources/batches.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/test_client_batches.py; git diff --check.
  - Commit: feat(resources): add batches resource
  - Замечания: low-level batches API, docs/notebooks и следующие срезы не менялись.
- 2026-04-27: завершён срез 4.
  - Что сделано: добавлен notebook с batch flow через `client.batches`, README-пример и mapping для batch root shims.
  - Изменённые файлы: examples/example_batching.ipynb, examples/README.md, README.md, MIGRATION_GUIDE.md, MIGRATION_GUIDE_ru.md, docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md.
  - Тесты: node -e "JSON.parse(require('fs').readFileSync('examples/example_batching.ipynb','utf8')); console.log('ok')"; git diff --check; uv run ruff check README.md MIGRATION_GUIDE.md MIGRATION_GUIDE_ru.md examples/README.md.
  - Commit: docs(batches): add resource batch example
  - Замечания: `ruff check` неприменим к Markdown-файлам и падает на markdown syntax; file content API не добавлялся, `files.retrieve_content` указан только как future path в notebook markdown.
- 2026-04-27: завершён срез 5.
  - Что сделано: добавлены модель `File`, low-level file content helpers и deprecated aliases `get_image_sync`/`get_image_async`.
  - Изменённые файлы: src/gigachat/api/files.py, src/gigachat/models/files.py, src/gigachat/models/__init__.py, src/gigachat/__init__.py, src/gigachat/resources/files.py, tests/unit/gigachat/api/test_files.py, tests/unit/gigachat/models/test_files.py, docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md.
  - Тесты: uv run pytest tests/unit/gigachat/api/test_files.py -q; uv run pytest tests/unit/gigachat/models/test_files.py -q; uv run pytest tests/unit/gigachat/test_client_files.py -q; uv run pytest tests/unit/gigachat/test_client_resource_shims.py -q; uv run ruff check src/gigachat/api/files.py src/gigachat/models/files.py src/gigachat/resources/files.py tests/unit/gigachat/api/test_files.py tests/unit/gigachat/models/test_files.py; git diff --check.
  - Commit: feat(files): add low-level file content api
  - Замечания: `client.files.retrieve_content` и root `get_file_content` не добавлялись; `resources/files.py` изменён только для подавления fallout от deprecated low-level alias и сохранения текущего `retrieve_image` поведения до среза 6.
- 2026-04-27: завершён срез 6.
  - Что сделано: добавлены `files.retrieve_content`/`a_files.retrieve_content`, root shims `get_file_content`/`aget_file_content`, а `get_image`/`aget_image` и resource aliases `retrieve_image` переведены на generic content path.
  - Изменённые файлы: src/gigachat/resources/files.py, src/gigachat/client.py, tests/unit/gigachat/test_client_files.py, tests/unit/gigachat/test_client_resource_shims.py, docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md.
  - Тесты: uv run pytest tests/unit/gigachat/test_client_files.py -q; uv run pytest tests/unit/gigachat/test_client_resource_shims.py -q; uv run pytest tests/unit/gigachat/test_client_lifecycle.py -q; uv run ruff check src/gigachat/resources/files.py src/gigachat/client.py tests/unit/gigachat/test_client_files.py tests/unit/gigachat/test_client_resource_shims.py; git diff --check.
  - Commit: feat(resources): add file content resource
  - Замечания: `retrieve_image` теперь warning-ит как deprecated image-only alias, поэтому тесты обновлены на expected warning и canonical `retrieve_content` без warning.
- 2026-04-27: завершён срез 7.
  - Что сделано: добавлены модели function validation и low-level helpers для `POST /functions/validate`.
  - Изменённые файлы: src/gigachat/api/tools.py, src/gigachat/models/tools.py, src/gigachat/models/__init__.py, src/gigachat/__init__.py, tests/unit/gigachat/api/test_tools.py, tests/unit/gigachat/models/test_tools.py, docs/internal/RESOURCE_API_BATCHES_FILES_PROGRESS.md.
  - Тесты: uv run pytest tests/unit/gigachat/api/test_tools.py -q; uv run pytest tests/unit/gigachat/models/test_tools.py -q; uv run ruff check src/gigachat/api/tools.py src/gigachat/models/tools.py tests/unit/gigachat/api/test_tools.py tests/unit/gigachat/models/test_tools.py; git diff --check.
  - Commit: feat(functions): add low-level function validation api
  - Замечания: `client.functions.validate` и root shims не добавлялись; это следующий срез.
