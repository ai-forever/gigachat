# Refactoring Notes

**Note**: All information in this file must be grouped by specific issues. Do not separate problems and solutions into different sections; keep them together under the relevant issue heading.

## Resource Leak in Hybrid Client
- **Problem**: The `GigaChat` class inherits from both `GigaChatSyncClient` and `GigaChatAsyncClient`. Instantiating `GigaChat()` triggers `__init__` for both, creating **four** clients immediately (sync client, sync auth client, async client, async auth client).
- **Leak Analysis**:
  - **Sync Context Manager** (`with GigaChat() as giga`):
    - calls `__enter__` (returns self) and `__exit__`.
    - `__exit__` calls `close()` which closes only sync clients.
    - Async clients (`_aclient`, `_auth_aclient`) created in `__init__` are never closed and remain open until GC.
  - **Async Context Manager** (`async with GigaChat() as giga`):
    - calls `__aenter__` (returns self) and `__aexit__`.
    - `__aexit__` calls `aclose()` which closes only async clients.
    - Sync clients (`_client`, `_auth_client`) created in `__init__` are never closed.
  - **Manual Usage**:
    - User must know implementation details to call both `close()` and `aclose()` to fully clean up.
    - Common pattern `giga.close()` leaks async resources.
  - **Solution (Lazy Initialization)**:
    - **Implementation Details**:
      - Refactored `GigaChatSyncClient` and `GigaChatAsyncClient` to remove eager instantiation of `httpx` clients in `__init__`.
      - Introduced private attributes (e.g., `_client_instance`) initialized to `None`.
      - Implemented properties (e.g., `@property def _client(self)`) that instantiate the `httpx.Client` only upon first access.
      - Updated `close()` and `aclose()` methods to check if the client instances exist (are not `None`) before attempting to close them.
    - **Why**:
      - **Resource Efficiency**: The hybrid `GigaChat` class inherits from both sync and async clients. Previously, this caused all 4 underlying connections to open immediately. Lazy initialization ensures only the requested type (sync or async) creates connections.
      - **Leak Prevention**: Prevents the scenario where using `with GigaChat() as giga:` would clean up sync clients but leave async clients open (leaking sockets), as the async clients are now never created in that workflow.
- **Status**: Resolved. Lazy initialization implemented for both sync and async clients.
- **Benefit**: Users of one paradigm (sync or async) never create the other's resources, preventing leaks.

## API Layer Fragmentation
- **Problem**: The API layer is fragmented with a "one file per endpoint" pattern (approx. 20 files in `src/gigachat/api/`), which clutters the directory structure and separates logically related functionality (e.g., file handling is split across 5 different files).
- **Solution (Consolidation)**:
  - **Implementation Details**:
    - Grouped individual API endpoint files into domain-specific modules within `src/gigachat/api/`:
      - `chat.py`: Combined `post_chat` and `stream_chat`. Renamed functions to `chat_sync`, `chat_async`, `stream_sync`, `stream_async`.
      - `files.py`: Combined `get_file`, `get_files`, `post_files`, `post_files_delete`, `get_image`. Renamed functions to `get_file_sync/async`, `upload_file_sync/async`, etc.
      - `models_controller.py`: Combined `get_model` and `get_models`. Renamed to `get_model_sync/async` and `get_models_sync/async`.
      - `auth.py`: Combined `post_auth` and `post_token`. Renamed to `auth_sync/async` and `token_sync/async`.
      - `tools.py`: Combined `post_tokens_count`, `post_functions_convert`, `post_ai_check`, `post_embeddings`, `get_balance`. Renamed to `tokens_count_sync/async`, etc.
    - Updated `GigaChatSyncClient` and `GigaChatAsyncClient` in `src/gigachat/client.py` to use the new modules and function names.
    - Merged corresponding unit tests into `test_chat.py`, `test_auth.py`, and `test_models_controller.py`.
    - Deleted the old fragmented files and updated `src/gigachat/api/__init__.py`.
  - **Why**:
    - **Cohesion**: Related functionality is now located in a single file, making it easier to understand and maintain the domain logic.
    - **Navigability**: Reduced the number of files in `src/gigachat/api/` from ~20 to 5, making the project structure cleaner.
- **Status**: Resolved. API layer consolidated.

## API Model Naming Consistency
- **Problem**: The file `src/gigachat/api/models_controller.py` had an inconsistent suffix `_controller` compared to other API modules (`chat.py`, `files.py`) to avoid conflict with `src/gigachat/models` package.
- **Solution**:
  - Renamed `src/gigachat/api/models_controller.py` to `src/gigachat/api/models.py`.
  - Updated imports in `src/gigachat/client.py` and tests to allow `gigachat.api.models` and `gigachat.models.models` to coexist.
  - **Why**: Ensures consistent naming across all API layer files (`api/<domain>.py`).
- **Status**: Resolved.

## Assistants and Threads API Consolidation
- **Problem**: The `assistants` and `threads` API modules were fragmented into multiple files within `src/gigachat/api/assistants/` and `src/gigachat/api/threads/` directories, following an obsolete "one file per endpoint" pattern.
- **Solution**:
  - **Implementation Details**:
    - Consolidated `src/gigachat/api/assistants/*.py` into a single module `src/gigachat/api/assistants.py`.
    - Consolidated `src/gigachat/api/threads/*.py` into a single module `src/gigachat/api/threads.py`.
    - Updated `src/gigachat/assistants.py` and `src/gigachat/threads.py` client wrappers to use the new consolidated modules.
    - Fixed missing methods and ensured backward compatibility in `src/gigachat/threads.py` (e.g., `list`, `retrieve`, `delete`, `run_stream`, etc.) matching the new API structure.
    - Removed the now empty `src/gigachat/api/assistants/` and `src/gigachat/api/threads/` directories.
  - **Why**:
    - **Consistency**: Aligns `assistants` and `threads` with the rest of the API layer (`chat.py`, `files.py`, etc.).
    - **Maintainability**: Reduces file count and simplifies imports.
- **Status**: Resolved.

## Pydantic Models Consolidation
- **Problem**: The Pydantic models in `src/gigachat/models/` were fragmented into many small files (one per class), making the directory cluttered and imports verbose.
- **Solution**:
  - **Implementation Details**:
    - Grouped related models into domain-specific modules within `src/gigachat/models/`:
      - `chat.py`: `Chat`, `ChatCompletion`, `Messages`, `Choices`, `Usage`, `Function`, `FunctionCall`, `Storage`, etc.
      - `files.py`: `UploadedFile`, `UploadedFiles`, `DeletedFile`, `Image`.
      - `models.py`: `Model`, `Models`.
      - `auth.py`: `AccessToken`, `Token`.
      - `tools.py`: `AICheckResult`, `Balance`, `TokensCount`, `OpenApiFunctions`.
      - `embeddings.py`: `Embedding`, `Embeddings`, `EmbeddingsUsage`.
      - `assistants.py`: `Assistant`, `AssistantAttachment`, `AssistantDelete`, etc.
      - `threads.py`: `Thread`, `ThreadMessage`, `ThreadRunResult`, etc.
      - `utils.py`: `WithXHeaders`.
    - Separated embeddings API from `tools.py` into `src/gigachat/api/embeddings.py` to match the model structure.
    - Updated `src/gigachat/models/__init__.py` to export from new locations.
    - Removed fragmented files and directories.
  - **Why**:
    - **Consistency**: Aligns the models structure with the API layer structure.
    - **Cleanliness**: Reduces the number of files in `src/gigachat/models/` significantly.
- **Status**: Resolved.

## API Response Handling Consolidation
- **Problem**: The API layer contained significant code duplication in handling HTTP responses (validating status codes, parsing content) and managing streaming responses (iterating over SSE events). This logic was repeated across multiple API modules (`chat.py`, `threads.py`, `assistants.py`, etc.).
- **Solution**:
  - **Implementation Details**:
    - Centralized response validation (`_check_response`, `_acheck_response`) and generic request/stream execution helpers into `src/gigachat/api/utils.py`.
    - Created `execute_request_sync`, `execute_request_async`, `execute_stream_sync`, and `execute_stream_async` functions to handle the boilerplate of making requests and parsing responses.
    - Refactored all API modules (`chat.py`, `threads.py`, `assistants.py`, `files.py`, `models.py`, `tools.py`, `auth.py`, `embeddings.py`) to use these new helpers.
    - Fixed an issue with `async def` stream wrappers returning coroutines instead of async iterators by changing them to regular `def` functions that return the generator object directly.
  - **Why**:
    - **Reduces Duplication**: Eliminates repetitive code for error handling and response parsing.
    - **Consistency**: Ensures all endpoints handle HTTP errors (e.g., 401 Unauthorized) and content types uniformly.
    - **Maintainability**: Future changes to response processing (e.g., handling 429 Rate Limits) only need to be applied in one place (`utils.py`).
- **Status**: Resolved.

## Unit Test Consolidation
- **Problem**: The unit tests were fragmented and inconsistent. `test_client.py` was a monolithic file >750 lines covering multiple domains. Some tests were loose files in `tests/unit_tests/gigachat/` while others were in `tests/unit_tests/gigachat/api/`.
- **Solution**:
  - **Implementation Details**:
    - Broke down `test_client.py` into domain-specific test files: `test_client_chat.py`, `test_client_files.py` (merged `test_get_image.py`), `test_client_models.py`, `test_client_tools.py`, `test_client_embeddings.py`.
    - Renamed `test_assistants.py` to `test_client_assistants.py` and `test_threads.py` to `test_client_threads.py`.
    - Cleaned up dead code (`test_models.py`).
  - **Why**:
    - **Maintainability**: Smaller, focused test files are easier to read and maintain.
    - **Consistency**: Aligns the test structure with the recently refactored source code structure.
    - **Clarity**: Distinctly separates High-Level Client tests (`test_client_*.py`) from Low-Level API tests (`api/test_*.py`).
- **Status**: Resolved.

## Authentication and Stream Logic Improvements
- **Problem**: The current authentication logic is reactive (waits for 401 error) rather than proactive (checking expiration), causing unnecessary failed requests. Additionally, streaming methods cannot use the standard `_decorator` for auth retries, leading to significant code duplication across `client.py` and `threads.py` (same try/except block repeated 6+ times).
- **Solution (Stream Decorator & Proactive Auth)**:
  - **Implementation Details**:
    - **Proactive Auth**: Updated `_check_validity_token` to check `self._access_token.expires_at` against current time, refreshing before the token actually expires (1 minute buffer). Handled edge case `expires_at=0` (manual tokens) by treating them as valid until proven otherwise.
    - **Stream Decorator**: Created `_stream_decorator` (sync) and `_astream_decorator` (async) in `client.py`. These decorators wrap the generator returned by streaming methods. They encapsulate the retry logic: try to yield from the generator, if `AuthenticationError` occurs, reset token, refresh token, and retry.
    - **Refactoring**: Refactored `GigaChatSyncClient.stream`, `GigaChatAsyncClient.astream`, and all streaming methods in `ThreadsSyncClient` and `ThreadsAsyncClient` (`run_stream`, `run_messages_stream`, `rerun_messages_stream`) to use these new decorators. Removed approximately 100 lines of duplicated error handling code.
  - **Why**:
    - **Performance**: Proactive checks avoid the latency of a failed 401 request for most cases.
    - **Maintainability**: Centralizing stream retry logic removes massive duplication and ensures consistent behavior across all streaming endpoints. Any future changes to retry logic only need to happen in the decorators.
- **Status**: Resolved. All stream methods refactored and verified.

## Thread Safety and Cleanup Improvements
- **Problem**: The introduction of lazy initialization in the hybrid `GigaChat` client introduced a race condition where multiple threads accessing `_client` simultaneously could create multiple `httpx.Client` instances, causing resource leaks. Additionally, `aclose()` in the hybrid client only closed async resources, potentially leaking sync resources if both were used.
- **Solution (Thread Safety & Full Cleanup)**:
  - **Implementation Details**:
    - **Centralization**: Moved `GigaChat` class from `__init__.py` to `client.py` to better manage inheritance and overrides.
    - **Thread Safety**: Implemented Double-Checked Locking in `GigaChatSyncClient` lazy properties (`_client`, `_auth_client`) using `_sync_token_lock` to ensure only one client instance is created even under heavy concurrency. Switched to `threading.RLock` to prevent deadlocks in re-entrant calls.
    - **Cleanup**: Overrode `aclose()` in `GigaChat` to explicitly call `self.close()` (sync cleanup) in addition to `super().aclose()`, ensuring all resources (sync and async) are released when using `async with`.
    - **Testing**: Consolidated lazy init and thread safety tests into `tests/unit_tests/gigachat/test_client_lifecycle.py` and fixed Ruff warnings.
  - **Why**:
    - **Robustness**: Prevents race conditions and resource leaks in multi-threaded environments.
    - **Correctness**: Ensures that `async with GigaChat()` fully cleans up the object regardless of how it was used (sync or async).
    - **Stability**: Using `RLock` prevents deadlocks when internal methods call public methods that also require the lock.
- **Status**: Resolved.

## Pydantic Compatibility Layer Hardening
- **Problem**: `gigachat` uses a Pydantic compatibility layer (`src/gigachat/pydantic_v1/__init__.py`) with `import *` and explicit exclusion from `mypy` checks. This creates a blind spot for type safety and hides potential compatibility issues. Fully upgrading to Pydantic 2+ is not yet safe due to ecosystem fragmentation (dependencies like LangChain v0.2 pinned to Pydantic 1.x) and public API usage of V1 methods (e.g. `model.dict()`).
- **Solution (Hardening)**:
  - **Implementation Details**:
    - **Refactor Init**: Replace `import *` in `src/gigachat/pydantic_v1/__init__.py` with explicit exports (`BaseModel`, `Field`, `BaseSettings`, `root_validator`) to support static analysis.
    - **Enable Type Checking**: Removed `exclude = "src/gigachat/pydantic_v1"` from `pyproject.toml` to enable `mypy` validation.
    - **Cleanup**: Deleted unused proxy files `src/gigachat/pydantic_v1/main.py` and `dataclasses.py`.
    - **Fix Typing**: Resolved type errors in compatibility layer and `src/gigachat/models/chat.py`. Cleaned up unused ignores in `utils.py`.
  - **Why**:
    - **Safety**: Ensures the compatibility layer is robust and correctly typed.
    - **Preparedness**: Makes future migration to native Pydantic 2 easier by strictly defining the V1 interface usage.
    - **Developer Experience**: Improves IDE autocompletion and error checking.
- **Status**: Resolved.

## Linting and Code Quality Improvements
- **Problem**: The project had accumulated linting warnings (`ruff`) that were blocking a "clean" build state. Specifically, `src/gigachat/__init__.py` had unused imports (F401), `src/gigachat/threads.py` had unused imports (F401) and shadowed builtins (A003), and the `pydantic_v1` compatibility layer was excluded from coverage reports, hiding potential testing gaps.
- **Solution (Fix Linting Errors)**:
  - **Implementation Details**:
    - **Fix Imports**: Added `__all__` to `src/gigachat/__init__.py` to correctly export client classes. Removed unused `AuthenticationError` import from `src/gigachat/threads.py`.
    - **Suppress Warnings**: Added `# noqa: A003` to `list()` methods in `src/gigachat/threads.py` to explicitly allow shadowing the `list` builtin, preserving the API.
    - **Enable Coverage**: Removed `omit = ["*/pydantic_v1/*"]` from `pyproject.toml` to enable coverage reporting for the compatibility layer.
    - **Verify**: Ran `ruff` and `mypy` to ensure no errors remained.
  - **Why**:
    - **Cleanliness**: Ensures the codebase is free of linter warnings, making it easier to spot real issues in the future.
    - **Correctness**: Explicit exports in `__init__.py` improve IDE support and prevent "unused import" false positives.
    - **Visibility**: Enabling coverage for `pydantic_v1` ensures that this critical compatibility layer is actually being tested.
- **Status**: Resolved.

## Authentication Refactoring (Decorators)
- **Problem**: The client classes (`GigaChatSyncClient`, `GigaChatAsyncClient`, `Threads*`, `Assistants*`) contained significant boilerplate and code duplication for authentication retries. Every API method manually wrapped its call in a lambda using a generic helper method (`_decorator`). This made the code noisy and tightly coupled the authentication retry logic (checking token validity, handling 401s) to the client classes.
- **Solution (Decorators & Protocols)**:
  - **Implementation Details**:
    - **New Module**: Created `src/gigachat/authentication.py` to house all authentication logic.
    - **Protocols**: Defined `AuthClientProtocol` and `AsyncAuthClientProtocol` using `typing.Protocol` and `@runtime_checkable`. This allows the decorators to interact with any client object that has the required auth methods (`_update_token`, etc.) without circular imports or rigid inheritance.
    - **Decorators**: Implemented 4 standard Python decorators:
      - `@_with_auth`: For synchronous request-response methods.
      - `@_with_auth_stream`: For synchronous streaming methods (generators).
      - `@_awith_auth`: For asynchronous request-response methods.
      - `@_awith_auth_stream`: For asynchronous streaming methods (async generators).
    - **Refactoring**: Replaced the manual `lambda` wrappers in `client.py`, `threads.py`, and `assistants.py` with these clean decorators.
    - **Dynamic Resolution**: Used helper functions `_get_auth_client` to dynamically find the authentication provider (self, self._client, or self.base_client), enabling the same decorator to work across all client types.
  - **Why**:
    - **Cleaner Code**: Removes hundreds of instances of boilerplate wrapper code (`return self._decorator(lambda: ...)`).
    - **Separation of Concerns**: Authentication logic is now isolated in its own module, adhering to the Single Responsibility Principle.
    - **Flexibility**: The Protocol-based approach allows any future client-like object to easily opt-in to authentication handling without inheritance.
- **Status**: Resolved.

## Documentation Standardization
- **Problem**: The documentation for models, API methods, and client wrappers was inconsistent, with a mix of Russian and English docstrings, and lacked a standard format.
- **Solution**:
  - **Implementation Details**:
    - **Translation**: Translated all docstrings in `src/gigachat/models/`, `src/gigachat/api/`, and client files (`client.py`, `threads.py`, `assistants.py`) to English.
    - **Standardization**: Applied Google Python Style Guide formatting to all docstrings.
    - **Imperative Mood**: Enforced imperative mood (e.g., "Return..." instead of "Returns...") for all function and method docstrings to maintain consistency. Enabled Ruff rule `D401` to prevent regressions.
  - **Why**:
    - **Consistency**: Ensures a uniform developer experience across the entire library.
    - **Accessibility**: English documentation makes the library accessible to a broader audience.
    - **Clarity**: Standardized formatting and imperative mood improve readability and professionalism.
- **Status**: Resolved.

## Explicit API Exports
- **Problem**: The `src/gigachat/api/__init__.py` file did not have an `__all__` definition, relying on implicit exports or just exposing everything.
- **Solution**:
  - Added explicit `__all__` in `src/gigachat/api/__init__.py` covering all submodules (`assistants`, `auth`, `chat`, `embeddings`, `files`, `models`, `threads`, `tools`, `utils`).
  - **Why**: Defines a clear public interface for the API layer.
- **Status**: Resolved.

## Client Internal Attribute Consistency
- **Problem**: The sub-clients (`ThreadsSyncClient`, `AssistantsSyncClient`, and their async counterparts) use inconsistent naming to reference the parent `GigaChat` client (`_client` vs `base_client`). This creates confusion (as `_client` also refers to the `httpx` client) and requires complex logic in the authentication decorator to resolve the auth provider.
- **Solution**:
  - **Implementation Details**:
    - Standardize on `_base_client` for all sub-clients.
    - Update `authentication.py` to resolve auth client via `_base_client`.
    - Refactor `threads.py` and `assistants.py` to use the new attribute name.
    - Simplify auth decorators logic (remove legacy checks).
  - **Why**:
    - **Consistency**: Uniform naming convention across the codebase.
    - **Clarity**: Distinguishes the parent GigaChat client (`_base_client`) from the underlying HTTP client (`_client`).
    - **Convention**: Adheres to Python's "weak internal use" underscore prefix convention.
- **Status**: Resolved.

## Exception Handling Improvements
- **Problem**: The current exception handling is minimal (`ResponseError` inherits from `Exception` without `__init__` parameters), making it difficult for users to access error details like status codes, response bodies, or headers without manual parsing of `e.args`. Additionally, there are no specific exception classes for common HTTP errors (e.g., `RateLimitError`, `BadRequestError`).
- **Solution**:
  - **Implementation Details**:
    - Update `ResponseError` to store `status_code`, `content`, `headers`, and `url` as attributes.
    - Implement `__str__` for human-readable error messages.
    - Create specific exception subclasses for common HTTP status codes:
      - `BadRequestError` (400)
      - `AuthenticationError` (401)
      - `ForbiddenError` (403)
      - `NotFoundError` (404)
      - `UnprocessableEntityError` (422)
      - `RateLimitError` (429) - with `retry_after` property
      - `ServerError` (5xx)
    - Update `api/utils.py` to raise these specific exceptions based on status codes.
    - Add new unit tests in `tests/unit_tests/gigachat/test_exceptions.py` and update existing tests.
  - **Why**:
    - **Developer Experience**: Provides structured access to error details, eliminating the need for `e.args` parsing.
    - **Robustness**: Enables users to implement cleaner retry logic and specific error handling (e.g., catching `RateLimitError` separate from `AuthenticationError`).
    - **Standardization**: Aligns with Python best practices and other popular API clients.
- **Status**: Resolved.

## Pydantic V2 Migration
- **Problem**: The project relies on Pydantic V1 compatibility layers, which are slower, less maintained, and increasingly out of step with the Python ecosystem (including key integrations like LangChain v0.3+ which are Pydantic V2-native).
- **Solution (Native Pydantic V2)**:
  - **Implementation Details**:
    - **Dependencies**: Updated `pyproject.toml` to require `pydantic >= 2` and added `pydantic-settings`.
    - **Cleanup**: Removed `src/gigachat/pydantic_v1` compatibility layer and leftover empty directories.
    - **Models**: Migrated all models in `src/gigachat/models/` to native V2 syntax (using `model_config`, `@model_validator`).
    - **Settings**: Migrated `Settings` to use `pydantic-settings`.
    - **API/Client**: Updated code to use V2 methods (`model_dump`, `model_validate`) instead of V1 methods (`dict`, `parse_obj`).
  - **Why**:
    - **Performance**: Pydantic V2 is significantly faster (5-50x) for validation and serialization.
    - **Ecosystem Alignment**: Ensures full compatibility with modern libraries like LangChain.
    - **Maintainability**: Removes technical debt associated with the V1 compatibility shim.
- **Status**: Resolved. Migrated to native Pydantic V2.

## Public API Exports
- **Problem**: The package's `src/gigachat/__init__.py` only exports client classes (`GigaChat`, `GigaChatSyncClient`, `GigaChatAsyncClient`). This forces users to use verbose, implementation-aware imports for commonly needed types:
  - Exceptions: `from gigachat.exceptions import AuthenticationError, RateLimitError`
  - Models: `from gigachat.models.chat import Chat, Messages, MessagesRole`
  - Context variables: `from gigachat.context import session_id_cvar`

  This creates several issues:
  - **Poor Discoverability**: Users cannot discover available types via IDE autocomplete on `from gigachat import`.
  - **Verbose Imports**: Every script requires multiple import statements from internal modules.
  - **Hidden Features**: The exception hierarchy (with `RateLimitError.retry_after`) and context variables for request tracing are effectively invisible to users.
  - **Unclear Public API**: Without explicit exports, users may accidentally depend on internal implementation details.

- **Solution (Tiered Public API Exports)**:
  - **Proposed Implementation**:
    - **Tier 1 (Essential)**: Export types fundamental to basic usage:
      - Exceptions: `GigaChatException`, `ResponseError`, `AuthenticationError`, `RateLimitError`
      - Core Models: `Chat`, `Messages`, `MessagesRole`, `ChatCompletion`, `ChatCompletionChunk`
    - **Tier 2 (Recommended)**: Export commonly needed types:
      - Additional Exceptions: `BadRequestError`, `ForbiddenError`, `NotFoundError`, `ServerError`
      - Function Calling: `Function`, `FunctionCall`, `FunctionParameters`
      - Response Components: `Choices`, `Usage`
      - Files/Embeddings: `Embeddings`, `Image`, `Model`, `Models`
      - Context Variables: `session_id_cvar`, `request_id_cvar`, `custom_headers_cvar`
    - **Not Exported**: Internal types remain accessible via submodule imports (`AccessToken`, `Token`, `WithXHeaders`, `Settings`, `Storage`, etc.)
    - Add explicit `__all__` to `src/gigachat/exceptions.py` and `src/gigachat/context.py` for clean re-exports.
  - **Why**:
    - **Developer Experience**: Enables clean single-line imports: `from gigachat import GigaChat, Chat, AuthenticationError`.
    - **Discoverability**: IDE autocomplete reveals available types when typing `from gigachat import `.
    - **API Contract**: Explicit `__all__` defines the public API boundary, making it clear what users can rely on.
    - **Unlocks Previous Work**: Makes the exception hierarchy (from "Exception Handling Improvements") and context variables actually usable.
    - **Backwards Compatible**: Purely additive change; existing imports continue to work.
- **Status**: Resolved.

## Automatic Retry Mechanism
- **Problem**: The library raises `RateLimitError` (429) and `ServerError` (5xx) immediately without any automatic retry capability. While `RateLimitError.retry_after` property exists, users must manually implement retry logic with exponential backoff. This is tedious and error-prone, especially for transient failures that would succeed on retry.
- **Solution (New Retry Decorator Layer)**:
  - **Implementation Details**:
    - **Settings**: Add new optional settings to `Settings` class:
      - `max_retries: int = 0` (disabled by default to avoid retry amplification with LangChain)
      - `retry_backoff_factor: float = 0.5`
      - `retry_on_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504)`
    - **New Module**: Create `src/gigachat/retry.py` with dedicated retry decorators:
      - `@_with_retry`: For synchronous request-response methods
      - `@_with_retry_stream`: For synchronous streaming methods (generators)
      - `@_awith_retry`: For asynchronous request-response methods
      - `@_awith_retry_stream`: For asynchronous streaming methods (async generators)
    - **Backoff Strategy**: Implement `_calculate_backoff()` with:
      - Exponential backoff: `base_delay * 2^attempt`
      - Jitter: Random 0-0.5s added to prevent thundering herd
      - Respect `RateLimitError.retry_after` when available
      - Maximum delay cap of 60 seconds
    - **Decorator Stacking**: Apply retry decorators on top of auth decorators:
      ```python
      @_with_retry   # Outer: handles transient errors (429, 5xx)
      @_with_auth    # Inner: handles authentication (401)
      def chat(self, payload): ...
      ```
    - **Settings Resolution**: Use `_get_retry_settings()` helper to resolve settings from any client type (direct client or sub-clients via `_base_client`).
  - **Why**:
    - **Separation of Concerns**: Retry logic is isolated from authentication logic, following Single Responsibility Principle.
    - **Composable**: Decorators can be stacked and applied selectively.
    - **No Breaking Changes**: Purely additive; `max_retries=0` default preserves current behavior.
    - **No New Dependencies**: Built from scratch (~80 LOC) instead of adding tenacity dependency.
    - **LangChain Compatible**: Disabled by default to avoid retry amplification when used with `langchain-gigachat`.
    - **Consistent Pattern**: Follows the same decorator pattern established for authentication.
  - **Design Decisions**:
    - **Default Disabled**: `max_retries=0` is safe for nested usage with LangChain's own retry mechanism.
    - **Build vs. Library**: Built from scratch to avoid adding dependencies and version conflicts.
    - **No Protocol Needed**: Unlike auth decorators, retry only reads settings (no method calls), so a simple `_get_retry_settings()` helper suffices.
- **Status**: Resolved. Retry decorators implemented and applied to all client methods in `GigaChatSyncClient`, `GigaChatAsyncClient`, `ThreadsSyncClient`, `ThreadsAsyncClient`, `AssistantsSyncClient`, and `AssistantsAsyncClient`. Unit tests added in `tests/unit_tests/gigachat/test_retry.py`.

## Migrate to uv + Ruff
- **Problem**: The current development workflow uses `poetry` (package management), `black` (formatting), and `ruff` (linting). This fragmentation leads to slower operations and requires maintaining multiple tool configurations. `poetry` resolution can be slow, and using separate tools for linting and formatting increases complexity.
- **Solution (Consolidated Toolchain)**:
  - **Tooling**:
    - **uv**: Replace `poetry` with `uv` for fast package management, dependency resolution, and virtual environment handling.
    - **ruff**: Use `ruff` for *both* linting and formatting, replacing `black`.
  - **Implementation Details**:
    - **Phase 1 (Format)**: Update `ruff` configuration to handle formatting (replaces `black`). Remove `black` dependency.
    - **Phase 2 (Migrate)**: Run `migrate-to-uv` to convert `pyproject.toml` to PEP 621 standard. Replace `poetry.lock` with `uv.lock`.
    - **Phase 3 (Hooks)**: Update pre-commit hooks to use `ruff-pre-commit` and `uv` commands.
    - **Phase 4 (Docs)**: Update documentation and CI/CD pipelines to reflect new commands (`uv sync`, `uv run`).
  - **Why**:
    - **Performance**: `uv` is significantly faster (10-100x) than Poetry.
    - **Simplicity**: Unifies formatting and linting under a single tool (`ruff`), reducing dependencies.
    - **Standards**: Adopts PEP 621 (`[project]` table) and PEP 735 (`[dependency-groups]`) for a modern, standardized project structure.
- **Status**: Resolved. Migrated to uv and Ruff.

## CI/CD Workflow Implementation
- **Problem**: The GitHub Actions workflow (`.github/workflows/gigachat.yml`) is a placeholder template that only prints "Hello, world!" and does not run any validation. This means:
  - No automated linting, type checking, or testing on pull requests.
  - All refactoring work has no regression protection.
  - The README displays a CI badge that references a non-functional workflow.
  - The new `uv` toolchain is not utilized in CI.
- **Solution (Functional CI Pipeline)**:
  - **Implementation Details**:
    - **Local Tooling Update**:
      - Added `pytest-cov` to dev dependencies in `pyproject.toml`.
      - Updated `Makefile` test target to use `pytest --cov=src --cov-report=term-missing`.
    - **CI Workflow** (`.github/workflows/gigachat.yml`):
      - **Two Jobs**: Separated into `lint` (runs once) and `test` (runs on matrix).
      - **uv Setup**: Use `astral-sh/setup-uv@v5` action with `enable-cache: true` and `cache-dependency-glob: "uv.lock"`.
      - **Python Matrix**: Test on Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 (stable) and 3.14 (with `continue-on-error: true` for early compatibility testing).
      - **Lint Job** (Python 3.12):
        1. `ruff format --check src tests` (format check first per best practice)
        2. `ruff check src tests` (linting)
        3. `mypy src tests` (type checking)
      - **Test Job** (Matrix): `pytest --cov=src --cov-report=term-missing --cov-report=xml`
    - **Triggers**: Workflow runs on push to `main` and on pull requests to `main`.
  - **Why**:
    - **Regression Protection**: Automated validation catches issues before they reach the main branch.
    - **Confidence**: Ensures all refactoring work (Pydantic V2, retry mechanism, exceptions, etc.) remains stable.
    - **Consistency**: Local development (`make test`) and CI use the same tools and commands.
    - **Speed**: `uv` is 10-100x faster than Poetry, making CI runs significantly quicker.
    - **Efficiency**: Lint/type-check runs once (not 7x), while tests run on all Python versions.
- **Status**: Resolved. CI/CD workflow implemented with linting, type checking, testing, and caching.

## Python 3.8 Type Hint Compatibility Fixes
- **Problem**: CI tests failed on Python 3.8 with `TypeError: 'type' object is not subscriptable` and `TypeError: 'dict' object is not subscriptable`. This is because generic aliases like `type[...]` and `dict[...]` were introduced in Python 3.9.
- **Solution**:
  - **Implementation Details**:
    - Replaced `type[ResponseError]` with `Type[ResponseError]` (from `typing`) in `tests/unit_tests/gigachat/test_exceptions.py`.
    - Replaced `dict[str, str]` with `Dict[str, str]` (from `typing`) in `tests/unit_tests/gigachat/api/test_chat.py`.
  - **Why**: Ensures the codebase is compatible with the project's minimum supported Python version (3.8).
- **Status**: Resolved.

## Test Suite Refactoring
- **Problem**: The test suite has accumulated several inconsistencies and gaps:
  1. **Inconsistent module naming**: Some client tests use `test_client_` prefix (e.g., `test_client_chat.py`) while others don't (e.g., `test_client.py`, `test_connection_limits.py`).
  2. **Relative imports**: All 12 test files use relative imports (`from ...utils import get_json`) which are harder to read and fragile to restructuring.
  3. **Configuration issues**: `pyproject.toml` has commented-out lines and missing `asyncio_mode = "auto"`, requiring `@pytest.mark.asyncio` on every async test (60 instances).
  4. **Duplicated constants**: `BASE_URL`, `AUTH_URL`, `CREDENTIALS` are duplicated across many test files.
  5. **Missing test coverage**: No API-level tests for `files.py`, `embeddings.py`, `tools.py`, `assistants.py`, `threads.py`. No tests for `context.py`, `authentication.py` decorators, or model validation.
  6. **Double underscore convention**: 8 test functions use `test__function_name` to test private functions - this is acceptable and self-documenting.
- **Solution (Comprehensive Test Refactoring)**:
  - **Implementation Details**:
    - **Naming**: Rename `test_client.py` → `test_client_core.py` and `test_connection_limits.py` → `test_client_connection_limits.py` for consistency with other client tests.
    - **Imports**: Update `pythonpath` to include project root, convert all relative imports to absolute (`from tests.utils import get_json`).
    - **Configuration**: Remove commented lines, add `asyncio_mode = "auto"`, remove redundant `@pytest.mark.asyncio` decorators.
    - **Constants**: Create `tests/constants.py` with shared test constants, update all test files to import from it.
    - **Fixtures**: Add shared fixtures to `conftest.py` (`base_url`, `mock_access_token`, `mock_credentials`).
    - **Coverage**: Add missing API tests (`test_files.py`, `test_embeddings.py`, `test_tools.py`, `test_assistants.py`, `test_threads.py`, `test_utils.py`), core tests (`test_context.py`, `test_authentication.py`), expand `test_settings.py`, add model validation tests.
  - **Why**:
    - **Consistency**: Uniform naming conventions improve navigability and maintainability.
    - **Readability**: Absolute imports are clearer and more explicit about dependencies.
    - **DRY**: Centralized constants and fixtures reduce duplication and maintenance burden.
    - **Coverage**: Complete API and core module tests ensure all refactored code is properly validated.
    - **Developer Experience**: `asyncio_mode = "auto"` eliminates boilerplate and reduces test verbosity.
- **Status**: Resolved. All test files renamed, configuration cleaned, imports converted to absolute, constants centralized in `tests/constants.py`, shared fixtures added to `conftest.py`, and comprehensive test coverage added for API layer (`test_files.py`, `test_embeddings.py`, `test_tools.py`, `test_assistants.py`, `test_threads.py`, `test_utils.py`), core modules (`test_context.py`, `test_authentication.py`, expanded `test_settings.py`), and models (`tests/unit_tests/gigachat/models/` with validation tests for chat, files, embeddings, assistants, threads, tools, and auth models). Test count increased from 186 to 333 tests. All `ruff check`, `mypy`, and `pytest` pass.

## Unused `verbose` Setting Cleanup
- **Problem**: The `verbose` setting exists in `Settings` class and is accepted as a parameter in `_BaseClient.__init__`, but it is **never used anywhere** in the codebase. All logging statements (`_logger.debug()`, `_logger.warning()`) execute unconditionally without checking this setting.
  - Location: `src/gigachat/settings.py` line 35: `verbose: bool = False`
  - Location: `src/gigachat/client.py` line 121: `verbose: Optional[bool] = None`
  - **User Impact**: Users may set `verbose=True` expecting debug output, but nothing happens. This violates the principle of least surprise.
- **Analysis**:
  - The setting was likely intended to control logging verbosity but was never implemented.
  - Existing debug logging uses standard Python `logging` module, which users can already configure via `logging.getLogger("gigachat").setLevel(logging.DEBUG)`.
  - Keeping unused parameters in the public API creates confusion and technical debt.
- **Solution (Remove Setting)**:
  - **Approach**: Remove the `verbose` setting entirely rather than implementing it, because:
    1. Users already have standard Python logging configuration as an alternative.
    2. Removing dead code is cleaner than adding complexity for a feature that was never needed.
    3. Minimal breaking change risk — the setting currently does nothing.
  - **Implementation**:
    - Remove `verbose: bool = False` from `src/gigachat/settings.py`.
    - Remove `verbose: Optional[bool] = None` parameter from `_BaseClient.__init__` in `src/gigachat/client.py`.
    - Remove `"verbose": verbose` from the kwargs dict in `_BaseClient.__init__`.
    - Update tests if any reference the `verbose` parameter.
  - **Why**:
    - **API Hygiene**: Public APIs should not accept parameters that have no effect.
    - **Clarity**: Removes confusion for users who might expect verbose mode to enable debug logging.
    - **Simplicity**: Eliminates dead code without adding new complexity.
- **Status**: Resolved. Removed `verbose` field from `Settings`, removed `verbose` parameter from `_BaseClient.__init__`, updated tests in `test_settings.py` to remove `verbose` assertions and repurpose `test_bool_conversion` to use `verify_ssl_certs`. All 333 tests pass.
