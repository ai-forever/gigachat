# Refactoring Progress

## General
- [x] Initial setup

## Resource Leak in Hybrid Client
- [x] Fix Resource Leak in Hybrid Client (Lazy Initialization)
  - [x] Refactor `GigaChatSyncClient` to use lazy initialization for `_client` and `_auth_client`
  - [x] Refactor `GigaChatAsyncClient` to use lazy initialization for `_aclient` and `_auth_aclient`
  - [x] Update `close()` and `aclose()` to only close initialized clients
  - [x] Add regression test `tests/unit_tests/gigachat/test_lazy_init.py`

## API Layer Fragmentation
- [x] Consolidate API Layer
  - [x] Group chat endpoints into `chat.py`
  - [x] Group file endpoints into `files.py`
  - [x] Group model endpoints into `models_controller.py`
  - [x] Group auth endpoints into `auth.py`
  - [x] Group utility endpoints into `tools.py`
  - [x] Separate embeddings API from `tools.py` into `src/gigachat/api/embeddings.py`
  - [x] Update `Client` to use new structure
  - [x] Cleanup old files

## API Model Naming Consistency
- [x] Rename `models_controller.py` to `models.py`
  - [x] Rename file `src/gigachat/api/models_controller.py` to `src/gigachat/api/models.py`
  - [x] Update imports in `src/gigachat/client.py`
  - [x] Rename and update test `tests/unit_tests/gigachat/api/test_models.py`

## Assistants and Threads API Consolidation
- [x] Consolidate Assistants API
  - [x] Merge `src/gigachat/api/assistants/*.py` into `src/gigachat/api/assistants.py`
  - [x] Update `src/gigachat/assistants.py` to use new module
  - [x] Delete `src/gigachat/api/assistants/`
- [x] Consolidate Threads API
  - [x] Merge `src/gigachat/api/threads/*.py` into `src/gigachat/api/threads.py`
  - [x] Update `src/gigachat/threads.py` to use new module
  - [x] Delete `src/gigachat/api/threads/`

## Pydantic Models Consolidation
- [x] Consolidate Pydantic Models
  - [x] Group chat models into `src/gigachat/models/chat.py`
  - [x] Group file models into `src/gigachat/models/files.py`
  - [x] Group model models into `src/gigachat/models/models.py`
  - [x] Group auth models into `src/gigachat/models/auth.py`
  - [x] Group tool models into `src/gigachat/models/tools.py`
  - [x] Group embeddings models into `src/gigachat/models/embeddings.py`
  - [x] Group assistants models into `src/gigachat/models/assistants.py`
  - [x] Group threads models into `src/gigachat/models/threads.py`
  - [x] Group common models into `src/gigachat/models/utils.py`
  - [x] Update `src/gigachat/models/__init__.py`
  - [x] Update imports in codebase
  - [x] Delete old files and directories
