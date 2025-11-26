# Refactoring Notes

**Note**: All information in this file must be grouped by specific issues. Do not separate problems and solutions into different sections; keep them together under the relevant issue heading.

## Critical Priority

### 1. Resource Leak in Hybrid Client
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
  - Remove client instantiation from `__init__`.
  - Use properties (`@property`) to initialize `_client`/`_auth_client` and `_aclient`/`_auth_aclient` only on first access.
  - Update `close()` and `aclose()` to check for existence before closing.
- **Benefit**: Users of one paradigm (sync or async) never create the other's resources, preventing leaks.

### 2. Reliability & Error Handling
- **Issues**:
  - **Lack of Retries**: There is no built-in retry mechanism for transient network errors (e.g., 502, 504, timeouts). Retries currently only exist for `AuthenticationError` (token refresh).
  - **Generic Exceptions**: The `ResponseError` is too generic. Users cannot easily distinguish between server errors, rate limits, or bad requests without parsing strings.
- **Proposed Solutions**:
  - **Enhanced Error Handling**:
    - Implement a retry decorator for idempotent operations on transient errors.
    - Subclass `ResponseError` into specific types (e.g., `RateLimitError`, `ServiceUnavailableError`).

## High Priority

### 3. Code Duplication (DRY Violation)
- **Issues**:
  - **Client Logic**: `GigaChatSyncClient` and `GigaChatAsyncClient` contain nearly identical logic for token management and decorators.
  - **API Layer**: Files in `src/gigachat/api/` duplicate the request construction and response handling logic for `sync` and `asyncio` functions.
  - **Risk**: Any fix applied to the sync path must be manually replicated in the async path, prone to human error.
- **Proposed Solutions**:
  - **Unify Request Logic**:
    - Extract request preparation (URL building, header generation, payload serialization) into shared, pure synchronous functions.
    - The Sync and Async clients should only handle the network I/O transport, delegating logic to these shared helpers.

### 4. Project Structure & Complexity
- **Issues**:
  - **Fragmentation**: The "One File Per Endpoint" pattern (e.g., `get_model.py`, `post_chat.py`) creates excessive file overhead for simple logic.
  - **Implicit State**: Heavy reliance on `contextvars` to pass configuration (like `chat_url`) is opaque and harder to debug than explicit argument passing.
  - **Circular Imports**: `src/gigachat/client.py` imports everything, leading to a monolithic dependency graph.
- **Proposed Solutions**:
  - **Refactor API Layer**:
    - Group related endpoints into logical modules (e.g., `api/chat.py`, `api/files.py`) instead of single-function files.
    - Remove `contextvars` in favor of passing a configuration object or explicit arguments.

## Medium Priority

### 5. Dependency Management
- **Issues**:
  - **Outdated Libraries**: `httpx` is pinned to `<1`.
  - **Pydantic Shim**: The custom Pydantic v1/v2 compatibility layer in `src/gigachat/pydantic_v1/` is fragile compared to standard solutions like `pydantic-settings`.
- **Proposed Solutions**:
  - **Modernization**:
    - Upgrade to `httpx >= 1.0`.
    - Migrate fully to Pydantic v2 conventions.

### 6. Type Safety
- **Issues**:
  - Usage of `cast(AccessToken, ...)` in `get_token` masks potential `None` values, bypassing static type safety.
