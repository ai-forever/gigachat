# v1.0 Migration Plan

**Purpose**: Track breaking changes and improvements deferred to the v1.0 release when backward compatibility breaks are allowed.

**Note**: All information in this file must be grouped by specific issues. Do not separate problems and solutions into different sections; keep them together under the relevant issue heading.

## Context

The `gigachat` package follows semantic versioning. Breaking changes to the public API require a major version bump (v1.0). This document tracks:
- Breaking changes that were analyzed but reverted to maintain backward compatibility
- API improvements that require breaking existing user code
- Cleanup tasks that remove deprecated functionality

These changes will be implemented when:
1. The `gigachat` package is ready for v1.0 release
2. Coordinated with `langchain-gigachat` v1.0 release
3. LangChain/LangGraph ecosystem is ready for major version updates

## Workflow

### Progress Tracking
- Tasks are grouped by issue.
- Only analyzed and approved issues are added to this plan.
- **Chronological Order**: All sections (issues) must be listed in chronological ascending order (oldest first). New tasks should always be added at the end.

### Implementation Process
1. When v1.0 development begins, create corresponding entries in `docs/TODO.md`.
2. Before implementing each breaking change, get approval.
3. After implementation, summarize results.
4. After solving each issue:
   - Update this file with final implementation details.
   - Update `docs/TODO.md` to reflect implemented steps.

---

## Planned Breaking Changes

### Remove Unused `verbose` Parameter
- **Problem**: The `verbose` parameter exists in `Settings` class and is accepted in `_BaseClient.__init__`, but it is **never used anywhere** in the `gigachat` codebase. All logging statements execute unconditionally without checking this setting.
  - Location: `src/gigachat/settings.py`: `verbose: bool = False`
  - Location: `src/gigachat/client.py`: `verbose: Optional[bool] = None` in `_BaseClient.__init__` and explicit `__init__` signatures
  - **User Impact**: Users may set `verbose=True` expecting debug output, but nothing happens in the `gigachat` SDK itself. However, `langchain-gigachat` uses this parameter for request/response logging.
- **Analysis**:
  - The setting was intended to control logging verbosity but was never implemented in the `gigachat` SDK.
  - The downstream `langchain-gigachat` package uses `verbose=True` to log requests and responses.
  - Existing debug logging in `gigachat` uses standard Python `logging` module, which users can configure via `logging.getLogger("gigachat").setLevel(logging.DEBUG)`.
  - Removing the parameter is a breaking change — existing user code with `GigaChat(verbose=True)` will raise `TypeError`.
- **Current State (v0.x)**:
  - Parameter is **restored and marked as deprecated** in docstrings: "Deprecated: will be removed in v1.0."
  - Parameter is accepted but ignored by the `gigachat` SDK.
  - Parameter is passed through to `langchain-gigachat` where it controls logging.
- **Solution (Remove in v1.0)**:
  - **Approach**: Remove the `verbose` setting entirely, because:
    1. Users can configure logging via standard Python `logging` module.
    2. Removing dead code is cleaner than maintaining unused parameters.
  - **Implementation**:
    - Remove `verbose: bool = False` from `src/gigachat/settings.py`.
    - Remove `verbose: Optional[bool] = None` parameter from `_BaseClient.__init__` in `src/gigachat/client.py`.
    - Remove `verbose` from explicit `__init__` signatures in `GigaChatSyncClient`, `GigaChatAsyncClient`, `GigaChat`.
    - Remove `"verbose": verbose` from the kwargs dict in `_BaseClient.__init__`.
  - **Why**:
    - **API Hygiene**: Public APIs should not accept parameters that have no effect.
    - **Clarity**: Removes confusion for users who might expect verbose mode to enable debug logging.
    - **Simplicity**: Eliminates dead code without adding new complexity.
- **Coordination**: Requires coordinated removal with `langchain-gigachat` v1.0.
- **Status**: Deprecated in v0.x. Planned removal in v1.0.
