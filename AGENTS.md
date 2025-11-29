# AGENTS.md

## Project Overview
GigaChat. Python-library for GigaChat API.

## Setup Commands
- Install dependencies: `uv sync`
- Activate shell: `source .venv/bin/activate`

## Build and Test Commands
- Run tests: `uv run pytest`
- Lint code: `uv run ruff check src`
- Format code: `uv run ruff format src`
- Type check: `uv run mypy src`

## Code Style Guidelines
- Max line length: 120
- Use `ruff` for formatting
- Use `ruff` for linting
- Use `mypy` in strict mode (plugin: pydantic.mypy)
- Do not add comments to the refactored code, only if it is completely necessary
- **Documentation**:
  - Language: English.
  - Style: Google Python Style Guide.
  - Mood: Imperative mood for functions/methods (e.g., "Return..." not "Returns...").
  - Detail: Explicitly state constraints, ranges, and allowed values for fields.

## Refactoring Documentation
- **Progress Tracking**: Refer to `docs/TODO.md` for the current status of refactoring tasks.
  - Tasks are grouped by issue.
  - Only analyzed and approved issues are added to the active plan.
  - **Chronological Order**: All sections (issues) must be listed in **chronological ascending order** (Oldest first).
    - This applies to both `docs/TODO.md` and `docs/REFACTORING.md`.
    - New tasks should always be added at the end of the list.
- **Refactoring Details**: Consult `docs/REFACTORING.md` for information on identified issues, chosen solutions, and other pertinent details related to the refactoring process.
  - Includes detailed analysis of issues and approved solutions.
  - **Workflow**:
    - Before implementing each todo item list, get approval.
    - After implementation, summarize results.
  - **After solving each issue**:
    - Add detailed information about the solution (why and how it was implemented in such way) to `docs/REFACTORING.md`.
    - Update `docs/TODO.md` to reflect detailed implemented steps within each issue section.


## AGENTS.md Purpose and Maintenance
- **Purpose**: This file serves as the primary source of truth for AI coding agents. It contains context, rules, and instructions that might be too detailed or operational for the human-facing `README.md`. It ensures agents have predictable, clear guidance on how to build, test, and modify the project.
- **When to Update**:
  - When build steps, test commands, or development environment setup changes.
  - When new coding conventions or architectural rules are adopted.
  - When the refactoring strategy or documentation structure evolves (as defined in the rules below).
- **Reference**: Follow the guidelines at [agents.md](https://agents.md) for structuring and maintaining this file.

## Documentation Updates
- Update only existing docs: `docs/REFACTORING.md`, `docs/TODO.md`, and `AGENTS.md`.
