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

## API Response Handling Consolidation
- [x] Update `src/gigachat/api/utils.py` with generic request/stream helpers
  - [x] Move `_check_response` and validation logic to utils
  - [x] Create `execute_request_sync` and `execute_request_async`
  - [x] Create `execute_stream_sync` and `execute_stream_async`
- [x] Refactor `src/gigachat/api/chat.py` to use new utils
- [x] Refactor `src/gigachat/api/threads.py` to use new utils
- [x] Refactor `src/gigachat/api/assistants.py` to use new utils
- [x] Refactor `src/gigachat/api/files.py` to use new utils
- [x] Refactor `src/gigachat/api/models.py` to use new utils
- [x] Refactor `src/gigachat/api/tools.py` to use new utils
- [x] Refactor `src/gigachat/api/auth.py` to use new utils
- [x] Refactor `src/gigachat/api/embeddings.py` to use new utils
- [x] Fix AsyncIterator/Coroutine mismatch in stream_async wrappers
  - [x] Update `src/gigachat/api/chat.py`: change `stream_async` to non-async def
  - [x] Update `src/gigachat/api/threads.py`: change async stream methods to non-async def
- [x] Verify all tests pass

## Unit Test Consolidation
- [x] Consolidate and Organize Unit Tests
  - [x] Remove empty file `tests/unit_tests/gigachat/test_models.py`
  - [x] Extract Chat tests from `test_client.py` to `test_client_chat.py`
  - [x] Extract Files tests to `test_client_files.py` (merge `test_get_image.py`)
  - [x] Extract Models tests from `test_client.py` to `test_client_models.py`
  - [x] Extract Tools tests from `test_client.py` to `test_client_tools.py`
  - [x] Extract Embeddings tests from `test_client.py` to `test_client_embeddings.py`
  - [x] Rename `test_assistants.py` to `test_client_assistants.py`
  - [x] Rename `test_threads.py` to `test_client_threads.py`
  - [x] Clean up remaining base tests in `test_client.py`
  - [x] Run all tests to ensure no regressions

## Authentication and Stream Logic Improvements
- [x] Refactor Authentication and Stream Logic
  - [x] Proactive Token Expiration Check (`_check_validity_token`)
  - [x] Implement `_stream_decorator` in `GigaChatSyncClient`
  - [x] Implement `_astream_decorator` in `GigaChatAsyncClient`
  - [x] Refactor `stream` methods to use stream decorators
  - [x] Verify refactoring

## Thread Safety and Cleanup Improvements
- [x] Fix Thread Safety and Cleanup in Hybrid Client
  - [x] Move `GigaChat` class from `__init__.py` to `client.py`
  - [x] Implement thread-safe lazy initialization (Double-Checked Locking)
  - [x] Update `GigaChat.aclose()` to close both sync and async clients
  - [x] Add tests for thread safety and cleanup

## Pydantic Compatibility Layer Hardening
- [x] Harden and Type-Check Pydantic Compatibility Layer
  - [x] Refactor `src/gigachat/pydantic_v1/__init__.py` for explicit exports
  - [x] Enable mypy for `pydantic_v1` in `pyproject.toml`
  - [x] Fix type errors in compatibility layer and models

## Linting and Code Quality Improvements
- [x] Fix Linting Errors and Enable Full Coverage
  - [x] Fix F401 errors in `src/gigachat/__init__.py` (add `__all__`)
  - [x] Fix F401 errors in `src/gigachat/threads.py` (remove unused imports)
  - [x] Suppress A003 errors in `src/gigachat/threads.py` for `list` methods
  - [x] Enable coverage for `src/gigachat/pydantic_v1/` in `pyproject.toml`
  - [x] Verify clean run of `ruff` and `mypy`
