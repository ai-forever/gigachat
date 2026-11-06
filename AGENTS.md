# AGENTS.md

Guidance for AI coding agents working with this repository.

## Project Overview

GigaChat Python SDK — a typed Python client for the GigaChat REST API (Sber's LLM). Supports Python 3.10+ with native HTTPX2. Published on PyPI as `gigachat`.

## Common Commands

```bash
make install           # Install deps (uv sync) + pre-commit hooks
make fmt               # Auto-format with Ruff
make lint              # Lint check
make mypy              # Type-check (strict mode)
make test              # Unit tests with coverage
make all               # lint + mypy + test (CI suite)
make test-integration  # Offline cassette replay (live network blocked)

# Run a single test
uv run pytest tests/unit/gigachat/test_client_chat.py::test_chat_completion

# Run tests matching a pattern
uv run pytest -k "test_retry"
```

Pre-commit hooks (ruff, mypy, trailing whitespace, etc.) run automatically on `git commit`. If a hook fails, fix and re-commit.

## Architecture

Layered design under `src/gigachat/`:

- **Client layer** (`client.py`): `GigaChat` (hybrid sync+async), `GigaChatSyncClient`, `GigaChatAsyncClient`, all inheriting from `_BaseClient`. HTTP clients are lazily initialized. Also contains `chat_parse()`/`achat_parse()` — structured output helpers that send a request with a JSON Schema `response_format`, then parse and validate the response against a Pydantic model.
- **API layer** (`api/`): One module per endpoint group (`chat.py`, `embeddings.py`, `files.py`, etc.). Functions take `httpx2.Client`/`AsyncClient` + params, return Pydantic models. Route through the shared `_execution.py` request policy.
- **Models layer** (`models/`): Pydantic V2 models for all requests/responses. Base class `APIResponse` carries `x_headers` metadata.
- **Auth/execution** (`_execution.py`): Shared token refresh and bounded request policy; compatibility protocol declarations remain in `authentication.py`. Supports OAuth credentials, user/password, mTLS, access token, and external Authorization overrides.
- **Retry** (`_execution.py`): Disabled by default, bounded by count/time/replayability, with a separate single authorized 401 replay. Never replay a stream after delivery begins. `retry.py` only classifies retryable failures.
- **Settings** (`settings.py`): `pydantic-settings` with `GIGACHAT_` env-var prefix.
- **Context variables** (`context.py`): Thread-safe `contextvars` for `session_id`, `request_id`, `client_id`, `authorization`, `custom_headers`.
- **Exceptions** (`exceptions.py`): Hierarchy rooted at `GigaChatException` → `ResponseError` → specific HTTP status exceptions.

## Key Conventions

- **Python 3.10 minimum**: Use builtin generics and union syntax (`dict[str, Any]`, `X | None`). Use HTTPX2 types at every SDK transport boundary; do not use global HTTPX aliases.
- **Ruff** for linting and formatting. Line length 120. Config in `pyproject.toml`.
- **mypy strict mode** with Pydantic plugin.
- **Minimal docstrings**: Imperative mood, one-line summary. No `Args:` section unless API is complex.
- **Commit messages**: Conventional commits format (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).
- **`additional_fields`** on `Chat` model: escape-hatch dict merged into the request JSON body via `_build_request_json()`. Explicit model fields always take precedence (merge order: `{**fields, **json_data}`).

## Testing

- **Unit tests** (`tests/unit/`): Mock HTTPX2 with `tests.httpx_mock.HTTPXMock` or `httpx2.MockTransport`. Both sync and async variants.
- **Integration tests** (`tests/integration/`): Recorded YAML cassettes replayed by the repository HTTPX2 adapter in `tests/integration/cassettes/`. Marked with `@pytest.mark.integration` and `@pytest.mark.vcr`. Excluded by default (`addopts = "-m 'not integration'"`).
- **Fixtures**: `tests/unit/conftest.py` (httpx_mock, base_url, credentials), `tests/integration/conftest.py` (gigachat_client, gigachat_async_client).
- **asyncio_mode = "auto"** — no need for `@pytest.mark.asyncio`.

## Adding a New API Endpoint

1. Pydantic models in `src/gigachat/models/`
2. API functions in `src/gigachat/api/` (sync + async endpoint contracts using the shared executor)
3. Client methods in `src/gigachat/client.py`, using `request_scope` for per-call options
4. Export in `src/gigachat/__init__.py` if user-facing
5. Unit tests in `tests/unit/gigachat/`

## Dependencies

Runtime: `httpx2`, `pydantic` (V2), `pydantic-settings`, `typing-extensions`. Optional extras: `aiohttp`, `http2`, `socks`. Keep minimal — justify any additions.

## HTTP lifecycle and migration

- Public RequestOptions must flow through every high-level endpoint; views share the owner's transport and token state.
- Injected HTTP clients are borrowed. The aiohttp adapter owns its lazy session. Close responses owned by streams without closing their shared client.
- Use Stream/AsyncStream context managers for deterministic early exit. Forward close/aclose through intermediate generators.
- Preserve constructor None defaults, primary model extras, native JSON Schema, and existing tuple parse returns.
- Do not log raw chunks, prompts, OAuth bodies, file bytes, or credentials.
- Read MIGRATION.md for HTTPX2/aiohttp capability boundaries. Offline replay must fail closed without live sockets.
