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

## Authentication Refactoring (Decorators)
- [x] Refactor Authentication to use Decorators
  - [x] Create `src/gigachat/authentication.py` to house authentication logic
  - [x] Implement Sync decorators: `@_with_auth` and `@_with_auth_stream`
  - [x] Implement Async decorators: `@_awith_auth` and `@_awith_auth_stream`
  - [x] Refactor `GigaChatSyncClient` and `GigaChatAsyncClient` to use new decorators
  - [x] Refactor `ThreadsSyncClient` and `ThreadsAsyncClient` to use new decorators
  - [x] Refactor `AssistantsSyncClient` and `AssistantsAsyncClient` to use new decorators
  - [x] Remove old `_decorator`, `_adecorator`, `_stream_decorator`, and `_astream_decorator` helper methods from client classes

## Documentation Standardization
- [x] Translate and Standardize Documentation
  - [x] Translate docstrings in `src/gigachat/models/` to English
  - [x] Translate docstrings in `src/gigachat/api/` to English
  - [x] Translate docstrings in `src/gigachat/client.py`, `threads.py`, `assistants.py` to English
  - [x] Standardize docstring formatting (Google style)
  - [x] Enforce imperative mood in docstrings (e.g. "Return" instead of "Returns")
  - [x] Enable Ruff rule D401 to enforce imperative mood

## Explicit API Exports
- [x] Add Explicit `__all__` Exports
  - [x] Update `src/gigachat/api/__init__.py` with `__all__`

## Client Internal Attribute Consistency
- [x] Standardize Internal Client Reference
  - [x] Update `src/gigachat/authentication.py` to support `_base_client`
  - [x] Refactor `AssistantsSyncClient` and `AssistantsAsyncClient` to use `_base_client` instead of `base_client`
  - [x] Refactor `ThreadsSyncClient` and `ThreadsAsyncClient` to use `_base_client` instead of `_client`
  - [x] Simplify auth decorators logic (remove legacy checks)
  - [x] Verify tests pass

## Exception Handling Improvements
- [x] Improve Exception Handling
  - [x] Refactor `ResponseError` to support structured attributes (`status_code`, `url`, `content`, `headers`)
  - [x] Implement `__str__` for `ResponseError`
  - [x] Implement specific exception subclasses: `BadRequestError` (400), `AuthenticationError` (401), `ForbiddenError` (403), `NotFoundError` (404), `UnprocessableEntityError` (422), `RateLimitError` (429), `ServerError` (5xx)
  - [x] Add helper properties to exceptions (e.g., `RateLimitError.retry_after`)
  - [x] Update `src/gigachat/api/utils.py` to raise specific exceptions
  - [x] Create unit tests `tests/unit_tests/gigachat/test_exceptions.py`
  - [x] Update existing tests

## Pydantic V2 Migration
- [x] Migrate to Pydantic V2
  - [x] Update dependencies in `pyproject.toml` (`pydantic >= 2`, `pydantic-settings`)
  - [x] Remove `pydantic_v1` compatibility layer
  - [x] Migrate models in `src/gigachat/models/` to V2 syntax
  - [x] Migrate settings in `src/gigachat/settings.py` to `pydantic-settings`
  - [x] Update client and API layer to use V2 methods (`model_dump`, `model_validate`)
  - [x] Update tests to support V2

## Public API Exports
- [x] Expand Package Public API
  - [x] Add `__all__` to `src/gigachat/exceptions.py`
  - [x] Add `__all__` to `src/gigachat/context.py`
  - [x] Update `src/gigachat/__init__.py`: import exceptions (Tier 1: `GigaChatException`, `ResponseError`, `AuthenticationError`, `RateLimitError`)
  - [x] Update `src/gigachat/__init__.py`: import exceptions (Tier 2: `BadRequestError`, `ForbiddenError`, `NotFoundError`, `ServerError`)
  - [x] Update `src/gigachat/__init__.py`: import core chat models (`Chat`, `Messages`, `MessagesRole`, `ChatCompletion`, `ChatCompletionChunk`)
  - [x] Update `src/gigachat/__init__.py`: import function calling models (`Function`, `FunctionCall`, `FunctionParameters`)
  - [x] Update `src/gigachat/__init__.py`: import response models (`Choices`, `Usage`)
  - [x] Update `src/gigachat/__init__.py`: import file/embedding models (`Embeddings`, `Image`, `Model`, `Models`)
  - [x] Update `src/gigachat/__init__.py`: import context variables (`session_id_cvar`, `request_id_cvar`, `custom_headers_cvar`)
  - [x] Update `src/gigachat/__init__.py`: define comprehensive `__all__` list
  - [x] Run `ruff check` to verify no linting errors
  - [x] Run `mypy` to verify type checking passes
  - [x] Run `pytest` to verify no test regressions

## Automatic Retry Mechanism
- [x] Implement Automatic Retry Mechanism
  - [x] Add retry settings to `Settings` class (`max_retries`, `retry_backoff_factor`, `retry_on_status_codes`)
  - [x] Update `_BaseClient.__init__` to accept and pass retry settings
  - [x] Create `src/gigachat/retry.py` module with `_get_retry_settings` helper
  - [x] Implement `_calculate_backoff()` with exponential backoff, jitter, and Retry-After support
  - [x] Implement `@_with_retry` decorator for sync request-response methods
  - [x] Implement `@_with_retry_stream` decorator for sync streaming methods
  - [x] Implement `@_awith_retry` decorator for async request-response methods
  - [x] Implement `@_awith_retry_stream` decorator for async streaming methods
  - [x] Apply `@_with_retry` to `GigaChatSyncClient` methods
  - [x] Apply `@_with_retry_stream` to `GigaChatSyncClient.stream` method
  - [x] Apply `@_awith_retry` to `GigaChatAsyncClient` methods
  - [x] Apply `@_awith_retry_stream` to `GigaChatAsyncClient.astream` method
  - [x] Apply retry decorators to `ThreadsSyncClient` methods
  - [x] Apply retry decorators to `ThreadsAsyncClient` methods
  - [x] Apply retry decorators to `AssistantsSyncClient` methods
  - [x] Apply retry decorators to `AssistantsAsyncClient` methods
  - [x] Create `tests/unit_tests/gigachat/test_retry.py` with unit tests for retry logic
  - [x] Run `ruff check`, `mypy`, and `pytest` to verify no regressions
  - [x] Update `docs/REFACTORING.md` with implementation details

## Migrate to uv + Ruff
- [x] Migrate to uv + Ruff (lint+format) + mypy
  - [x] Phase 1: Replace Black with Ruff Format
    - [x] Update `pyproject.toml`: new `[tool.ruff]` structure (`lint`, `format`)
    - [x] Remove `[tool.black]` and black dependency
    - [x] Update `Makefile` to use `ruff format`
    - [x] Run `ruff format` on codebase
  - [x] Phase 2: Migrate Package Manager (Poetry → uv)
    - [x] Run `uvx migrate-to-uv`
    - [x] Configure `pyproject.toml` (PEP 621, PEP 735)
    - [x] Replace `poetry.lock` with `uv.lock`
    - [x] Update `Makefile` to use `uv run`
  - [x] Phase 3: Update Pre-commit Configuration
    - [x] Add `ruff-pre-commit` hooks
    - [x] Update mypy hook to use `uv run`
  - [x] Phase 4: Documentation Updates
    - [x] Update `AGENTS.md`

## CI/CD Workflow Implementation
- [x] Implement CI/CD Workflow
  - [x] Add `pytest-cov` to dev dependencies in `pyproject.toml`
  - [x] Update `Makefile` test target to use `pytest --cov` with `term-missing` reporting
  - [x] Rewrite `.github/workflows/gigachat.yml` placeholder with actual CI workflow
  - [x] Add `uv` installation step using `astral-sh/setup-uv` action
  - [x] Configure Python version matrix (3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14 with allow-failure)
  - [x] Add linting job: `ruff format --check` and `ruff check` (format first, per best practice)
  - [x] Add type checking job: `mypy src tests`
  - [x] Add test job: `pytest --cov` with `term-missing` and `xml` coverage reporting
  - [x] Configure dependency caching for `uv` to speed up builds
  - [x] Verify workflow runs on push to main and pull requests

## Python 3.8 Type Hint Compatibility
- [x] Fix Python 3.8 compatibility issues
  - [x] Replace `type[...]` with `Type[...]` in `tests/unit_tests/gigachat/test_exceptions.py`
  - [x] Replace `dict[...]` with `Dict[...]` in `tests/unit_tests/gigachat/api/test_chat.py`

## Test Suite Refactoring
- [x] Module Naming Consistency
  - [x] Rename `test_client.py` to `test_client_core.py`
  - [x] Rename `test_connection_limits.py` to `test_client_connection_limits.py`
- [x] Configuration Cleanup
  - [x] Remove commented lines from `pyproject.toml` (`#show_missing`, `#skip_covered`)
  - [x] Add `asyncio_mode = "auto"` to `[tool.pytest.ini_options]`
  - [x] Remove `@pytest.mark.asyncio` decorators from all async tests (60 instances)
- [x] Absolute Imports
  - [x] Update `pythonpath` in `pyproject.toml` to include project root
  - [x] Convert relative imports to absolute imports in all 12 test files
- [x] Consolidate Constants and Fixtures
  - [x] Create `tests/constants.py` with shared `BASE_URL`, `AUTH_URL`, `CREDENTIALS`
  - [x] Update all test files to import from `tests/constants.py`
  - [x] Add shared fixtures to `tests/unit_tests/conftest.py`
- [x] Missing Test Coverage (API Layer)
  - [x] Create `tests/unit_tests/gigachat/api/test_files.py`
  - [x] Create `tests/unit_tests/gigachat/api/test_embeddings.py`
  - [x] Create `tests/unit_tests/gigachat/api/test_tools.py`
  - [x] Create `tests/unit_tests/gigachat/api/test_assistants.py`
  - [x] Create `tests/unit_tests/gigachat/api/test_threads.py`
  - [x] Create `tests/unit_tests/gigachat/api/test_utils.py`
- [x] Missing Test Coverage (Core Modules)
  - [x] Create `tests/unit_tests/gigachat/test_context.py`
  - [x] Create `tests/unit_tests/gigachat/test_authentication.py`
  - [x] Expand `test_settings.py` with comprehensive validation tests
- [x] Missing Test Coverage (Models)
  - [x] Create `tests/unit_tests/gigachat/models/` directory with model validation tests
- [x] Verification
  - [x] Run `ruff check`, `mypy`, and `pytest` to verify no regressions

## Unused `verbose` Setting Cleanup
- [x] Remove Unused `verbose` Setting
  - [x] Analyze current usage: `verbose` in `Settings` is accepted but never used
  - [x] Remove `verbose` field from `src/gigachat/settings.py`
  - [x] Remove `verbose` parameter from `_BaseClient.__init__` in `src/gigachat/client.py`
  - [x] Remove `verbose` from kwargs dict in `_BaseClient.__init__`
  - [x] Update/remove tests in `tests/unit_tests/gigachat/test_settings.py` if needed
  - [x] Run `ruff check`, `mypy`, and `pytest` to verify no regressions

## Negative `max_retries` Edge Case Fix
- [x] Handle Negative `max_retries` Values in Retry Decorators
  - [x] Update `_with_retry` to check `max_retries <= 0` instead of `== 0`
  - [x] Update `_with_retry_stream` to check `max_retries <= 0` instead of `== 0`
  - [x] Update `_awith_retry` to check `max_retries <= 0` instead of `== 0`
  - [x] Update `_awith_retry_stream` to check `max_retries <= 0` instead of `== 0`
  - [x] Remove dead code (`last_exception` variable and unreachable safety blocks)
  - [x] Remove unused `Optional` import
  - [x] Add `raise RuntimeError("Unreachable")` for type checker in non-generator decorators
  - [x] Add tests for negative `max_retries` behavior in `test_retry.py`
  - [x] Verify all tests pass

## GigaChat Constructor Argument Visibility
- [x] Add Explicit `__init__` Signatures for IDE Visibility
  - [x] Implementation
    - [x] Add explicit `__init__` to `GigaChatSyncClient` with all 22 params + `**kwargs: Any`
    - [x] Pass all explicit params + `**kwargs` to `super().__init__()` in `GigaChatSyncClient`
    - [x] Add explicit `__init__` to `GigaChatAsyncClient` with all 22 params + `**kwargs: Any`
    - [x] Pass all explicit params + `**kwargs` to `super().__init__()` in `GigaChatAsyncClient`
    - [x] Add explicit `__init__` to `GigaChat` with all 22 params + `**kwargs: Any`
    - [x] Pass all explicit params + `**kwargs` to `super().__init__()` in `GigaChat`
    - [x] Verify MRO chain: `GigaChat` → `GigaChatSyncClient` → `GigaChatAsyncClient` → `_BaseClient`
  - [x] Documentation
    - [x] Add class docstring with Args section to `GigaChatSyncClient`
    - [x] Add class docstring with Args section to `GigaChatAsyncClient`
    - [x] Add class docstring with Args section to `GigaChat`
  - [x] Verification
    - [x] Run `mypy` to verify type hints correctness
    - [x] Run `ruff check` to verify no linting errors
    - [x] Test IDE autocomplete for `GigaChat` constructor
    - [x] Test IDE autocomplete for `GigaChatSyncClient` constructor
    - [x] Test IDE autocomplete for `GigaChatAsyncClient` constructor
    - [x] Verify unknown kwargs warning still works (pass unknown param, check log)
  - [x] Testing
    - [x] Add unit test for `GigaChat` with all explicit params
    - [x] Add unit test for `GigaChat` with unknown kwargs (verify warning logged)
    - [x] Run `pytest` to verify no test regressions (339 passed)
  - [x] Finalization
    - [x] Update `docs/REFACTORING.md` with final implementation details

## `get_token()` Type Safety Fix
- [x] Fix `get_token()` and `aget_token()` Type Safety
  - [x] Analyze edge cases: OAuth, password, manual token, context var, no auth
  - [x] Change `get_token()` return type from `AccessToken` to `Optional[AccessToken]`
  - [x] Remove `cast(AccessToken, self._access_token)` in `get_token()`
  - [x] Return `self._access_token` directly (may be None for context var auth)
  - [x] Change `aget_token()` return type from `AccessToken` to `Optional[AccessToken]`
  - [x] Remove `cast(AccessToken, self._access_token)` in `aget_token()`
  - [x] Return `self._access_token` directly in `aget_token()`
  - [x] Update `get_token()` docstring: document None return for context var auth
  - [x] Update `aget_token()` docstring: document None return for context var auth
  - [x] Add unit test: `get_token()` with OAuth credentials returns AccessToken
  - [x] Add unit test: `get_token()` with password auth returns AccessToken
  - [x] Add unit test: `get_token()` with manual access_token returns AccessToken
  - [x] Add unit test: `get_token()` with authorization_cvar set returns None
  - [x] Add unit test: `get_token()` with no auth configured returns None
  - [x] Add unit test: `aget_token()` with OAuth credentials returns AccessToken
  - [x] Add unit test: `aget_token()` with password auth returns AccessToken
  - [x] Add unit test: `aget_token()` with manual access_token returns AccessToken
  - [x] Add unit test: `aget_token()` with authorization_cvar set returns None
  - [x] Add unit test: `aget_token()` with no auth configured returns None
  - [x] Run `ruff check`, `mypy`, and `pytest` to verify no regressions
  - [x] Update `docs/REFACTORING.md` with implementation details

## Token Caching Test Fix
- [x] Fix Token Caching Tests
  - [x] Identify root cause: proactive auth check with expired test timestamps
  - [x] Create explicit token test constants (`OAUTH_TOKEN_VALID`, `OAUTH_TOKEN_EXPIRED`, `PASSWORD_TOKEN_VALID`, `PASSWORD_TOKEN_EXPIRED`)
  - [x] Add pytest fixtures for token test data in `conftest.py`
  - [x] Add token reuse tests for OAuth credentials (sync and async)
  - [x] Add token reuse tests for password auth (sync and async)
  - [x] Add expired token refresh tests for OAuth credentials (sync and async)
  - [x] Add expired token refresh tests for password auth (sync and async)
  - [x] Refactor token tests to use fixtures
  - [x] Delete unused JSON files (`access_token.json`, `token.json`)
  - [x] Run `ruff check`, `mypy`, and `pytest` to verify no regressions (355 tests pass)

## Logging Improvements
- [x] Add NullHandler (Library Best Practice)
  - [x] Add `logging.getLogger(__name__).addHandler(logging.NullHandler())` to `src/gigachat/__init__.py`
- [x] Fix Authentication Error Log Level
  - [x] Change `logger.debug("AUTHENTICATION ERROR")` to `logger.warning(...)` in `src/gigachat/authentication.py` (4 occurrences)
  - [x] Improve message: `"Authentication failed (401), resetting token and retrying"`
- [x] Improve Token Update Messages
  - [x] Change `"OAUTH UPDATE TOKEN"` to `"Token refreshed via OAuth"` in `src/gigachat/client.py` (2 occurrences)
  - [x] Change `"UPDATE TOKEN"` to `"Token refreshed via password auth"` in `src/gigachat/client.py` (2 occurrences)
- [x] Remove Dead Code
  - [x] Remove unused logger definition from `src/gigachat/threads.py`
- [x] Rename Logger Variable
  - [x] Rename `_logger` to `logger` in `src/gigachat/client.py`
  - [x] Rename `_logger` to `logger` in `src/gigachat/authentication.py`
  - [x] Rename `_logger` to `logger` in `src/gigachat/retry.py`
  - [x] Rename `_logger` to `logger` in `src/gigachat/api/auth.py`
  - [x] Rename `_logger` to `logger` in `src/gigachat/api/utils.py`
- [x] Add Missing Warning Logs
  - [x] Add WARNING for 429 rate limit in `src/gigachat/api/utils.py` `_raise_for_status()` with Retry-After value
  - [x] Add WARNING for 5xx server errors in `src/gigachat/api/utils.py` `_raise_for_status()`
- [x] Add Retry Exhaustion Log
  - [x] Add INFO log in `src/gigachat/retry.py` when all retries exhausted (after final attempt)
- [x] Verification
  - [x] Run `ruff check`, `mypy`, and `pytest` to verify no regressions
