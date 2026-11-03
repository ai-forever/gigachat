# AGENTS.md

Guidance for AI coding agents working with this repository.

## Project Overview

GigaChat Python SDK — a typed Python client for the GigaChat REST API (Sber's LLM). Supports Python 3.8–3.13. Published on PyPI as `gigachat`.

## Common Commands

```bash
make install           # Install deps (uv sync) + pre-commit hooks
make fmt               # Auto-format with Ruff
make lint              # Lint check
make mypy              # Type-check (strict mode)
make test              # Unit tests with coverage
make all               # lint + mypy + test (CI suite)
make test-integration  # Integration tests (needs credentials or VCR cassettes)

# Run a single test
uv run pytest tests/unit/gigachat/test_client_chat.py::test_chat_completion

# Run tests matching a pattern
uv run pytest -k "test_retry"
```

Pre-commit hooks (ruff, mypy, trailing whitespace, etc.) run automatically on `git commit`. If a hook fails, fix and re-commit.

## Architecture

Layered design under `src/gigachat/`:

- **Client layer** (`client.py`): `GigaChat` (hybrid sync+async), `GigaChatSyncClient`, `GigaChatAsyncClient`, all inheriting from `_BaseClient`. HTTP clients are lazily initialized. Also contains `chat_parse()`/`achat_parse()` — structured output helpers that send a request with a JSON Schema `response_format`, then parse and validate the response against a Pydantic model.
- **API layer** (`api/`): One module per endpoint group (`chat.py`, `embeddings.py`, `files.py`, etc.). Functions take `httpx.Client`/`AsyncClient` + params, return Pydantic models. Decorated with `@_with_auth` and `@_with_retry`.
- **Models layer** (`models/`): Pydantic V2 models for all requests/responses. Base class `APIResponse` carries `x_headers` metadata.
- **Auth** (`authentication.py`): Decorator-based (`@_with_auth`, `@_awith_auth`). Auto-refreshes tokens on 401. Supports OAuth credentials, user/password, mTLS, access token, and context-variable overrides.
- **Retry** (`retry.py`): Decorator-based exponential backoff (`@_with_retry`). Decorator stacking order: retry wraps auth (`@_with_retry` above `@_with_auth`), so 401 auth errors trigger retry.
- **Settings** (`settings.py`): `pydantic-settings` with `GIGACHAT_` env-var prefix.
- **Context variables** (`context.py`): Thread-safe `contextvars` for `session_id`, `request_id`, `client_id`, `authorization`, `custom_headers`.
- **Exceptions** (`exceptions.py`): Hierarchy rooted at `GigaChatException` → `ResponseError` → specific HTTP status exceptions.

## Key Conventions

- **Python 3.8 compat required**: Use `typing.Dict`, `typing.List`, `typing.Optional`, `Type[X]` — not builtin generics or `X | Y` unions.
- **Ruff** for linting and formatting. Line length 120. Config in `pyproject.toml`.
- **mypy strict mode** with Pydantic plugin.
- **Minimal docstrings**: Imperative mood, one-line summary. No `Args:` section unless API is complex.
- **Commit messages**: Conventional commits format (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).
- **`additional_fields`** on `Chat` model: escape-hatch dict merged into the request JSON body via `_build_request_json()`. Explicit model fields always take precedence (merge order: `{**fields, **json_data}`).

## Testing

- **Unit tests** (`tests/unit/`): Mock HTTP with `pytest-httpx`. Both sync and async variants.
- **Integration tests** (`tests/integration/`): VCR cassettes (`vcrpy` + `pytest-recording`) in `tests/integration/cassettes/`. Marked with `@pytest.mark.integration` and `@pytest.mark.vcr`. Excluded by default (`addopts = "-m 'not integration'"`).
- **Fixtures**: `tests/unit/conftest.py` (httpx_mock, base_url, credentials), `tests/integration/conftest.py` (gigachat_client, gigachat_async_client).
- **asyncio_mode = "auto"** — no need for `@pytest.mark.asyncio`.

## Adding a New API Endpoint

1. Pydantic models in `src/gigachat/models/`
2. API functions in `src/gigachat/api/` (sync + async, with auth/retry decorators)
3. Client methods in `src/gigachat/client.py`
4. Export in `src/gigachat/__init__.py` if user-facing
5. Unit tests in `tests/unit/gigachat/`

## Dependencies

Runtime: `httpx`, `pydantic` (V2), `pydantic-settings`. Keep minimal — justify any additions.

## Cursor Cloud specific instructions

This repo is a **Python SDK** (no local API server). Development is `uv` + `make` only.

### Toolchain

- Install [uv](https://docs.astral.sh/uv/) if missing, then ensure `$HOME/.local/bin` is on `PATH`.
- `make install` runs `uv sync --group dev`. If `pre-commit install` fails because `core.hooksPath` is set, hooks are optional; use `uv run pre-commit run --all-files` when needed.
- All project commands should go through `uv run` or `make` so the `.venv` is used.

### Verification (matches CI)

| Check | Command |
|-------|---------|
| Lint + format | `make lint` |
| Types | `make mypy` |
| Unit tests | `make test` |
| Full CI suite | `make all` |
| Integration (VCR replay) | `CI=true env -u GIGACHAT_BASE_URL -u GIGACHAT_MODEL -u GIGACHAT_PROFANITY_CHECK -u GIGACHAT_VERIFY_SSL_CERTS -u GIGACHAT_USER -u GIGACHAT_PASSWORD make test-integration-ci` |

**VCR replay caveat:** Cassettes target `https://gigachat.devices.sberbank.ru/api/v1`. Injected Cloud secrets such as `GIGACHAT_BASE_URL` (IFT/staging) or `GIGACHAT_MODEL` change request bodies/hosts and break replay unless unset for that command (see `env -u` prefix above). Live calls can still use those variables.

### Live API smoke test (“hello world”)

With `GIGACHAT_USER` / `GIGACHAT_PASSWORD` (or `GIGACHAT_CREDENTIALS`) configured:

```bash
uv run python -c "
from gigachat import GigaChat
import os
with GigaChat(user=os.environ['GIGACHAT_USER'], password=os.environ['GIGACHAT_PASSWORD'], verify_ssl_certs=False) as c:
    print(c.chat('Привет! Ответь одним коротким предложением.').choices[0].message.content)
"
```

There is no `make run` or dev server; notebooks under `examples/` need Jupyter installed separately.
