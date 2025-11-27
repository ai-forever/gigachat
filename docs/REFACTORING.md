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
