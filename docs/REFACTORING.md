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
