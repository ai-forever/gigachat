# AGENTS.md

## Project Overview
GigaChat. Python-library for GigaChat API.

## Setup Commands
- Install dependencies: `poetry install`
- Activate shell: `poetry shell`

## Build and Test Commands
- Run tests: `poetry run pytest`
- Lint code: `poetry run ruff check src`
- Format code: `poetry run black src`
- Type check: `poetry run mypy src`

## Code Style Guidelines
- Max line length: 120
- Use `black` for formatting
- Use `ruff` for linting
- Use `mypy` in strict mode (plugin: pydantic.mypy)

## Refactoring Documentation
- **Progress Tracking**: Refer to `docs/TODO.md` for the current status of refactoring tasks.
- **Refactoring Details**: Consult `docs/REFACTORING.md` for information on identified issues, chosen solutions, and other pertinent details related to the refactoring process.

## Documentation Updates
- If there is a request to update existing docs, if required, only update `docs/REFACTORING.md`, `docs/TODO.md`, and `AGENTS.md` files.

