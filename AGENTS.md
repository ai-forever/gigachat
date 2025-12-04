# AGENTS.md

## Project Overview
Python SDK for the GigaChat LLM REST API.

### What This Library Does
- Provides sync (`GigaChatSyncClient`) and async (`GigaChatAsyncClient`) HTTP clients, plus hybrid `GigaChat` class
- Handles multiple auth methods: OAuth credentials, user/password, TLS certificates, manual access tokens
- Supports chat completions, streaming, embeddings, function calling, file operations, threads, and assistants
- Pydantic V2 models for all API requests/responses

### Key Modules
- `client.py` — Main client classes
- `api/` — Low-level HTTP functions (auth, chat, files, embeddings, models, threads, assistants, tools)
- `models/` — Pydantic V2 data models
- `authentication.py`, `retry.py` — Decorators for auth and retry logic
- `exceptions.py` — Exception hierarchy (AuthenticationError, RateLimitError, etc.)

## Setup Commands
- Install dependencies: `uv sync`
- Activate shell: `source .venv/bin/activate`

## Build and Test Commands
- Run tests: `uv run pytest`
- Lint code: `uv run ruff check src`
- Format code: `uv run ruff format src`
- Type check: `uv run mypy src`
- Verify all: `uv run ruff check src tests && uv run ruff format --check src tests && uv run mypy src && uv run pytest`

## Code Style
- Documentation: English, Google Python Style Guide, imperative mood ("Return..." not "Returns...")
- Avoid unnecessary comments

## Refactoring
See `docs/TODO.md` for task status and `docs/REFACTORING.md` for detailed analysis and solutions.
Update these docs after solving each issue.
