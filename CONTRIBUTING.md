# Contributing to GigaChat

Thank you for your interest in contributing to the GigaChat Python SDK! 🎉

We appreciate contributions of all kinds — bug reports, feature requests, documentation improvements, and code contributions. This guide will help you get started and ensure a smooth contribution process.

## Table of Contents

- [Types of Contributions](#types-of-contributions)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing](#testing)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Documentation Guidelines](#documentation-guidelines)
- [Project Architecture](#project-architecture)
- [License](#license)

## Types of Contributions

We welcome the following types of contributions:

- 🐛 **Bug Reports**: Help us identify and fix issues
- ✨ **Feature Requests**: Suggest new features or enhancements
- 📝 **Documentation**: Improve docs, examples, or guides
- 🧪 **Tests**: Add or improve test coverage
- 🔧 **Code**: Fix bugs, implement features, or refactor code
- 💡 **Ideas**: Share ideas for improvements in GitHub Discussions

Whether you're fixing a typo or implementing a major feature, all contributions are valued and appreciated!

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: Version 3.8 through 3.13 are supported
- **uv**: Modern Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Git**: For version control

### Development Setup

1. **Fork and clone the repository**

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/gigachat.git
cd gigachat
```

2. **Install dependencies and pre-commit hooks**

```bash
make install
```

This command will:
- Install all dependencies using `uv sync --group dev`
- Set up pre-commit hooks for automatic code quality checks

3. **Set up environment variables (for integration testing)**

Create a `.env` file in the project root:

```bash
# .env
GIGACHAT_CREDENTIALS=your_oauth_credentials_here
GIGACHAT_SCOPE=GIGACHAT_API_PERS
```

> **Note**: Integration tests are optional. See the [Testing](#testing) section for details.

4. **Configure SSL certificates**

The GigaChat API uses certificates issued by the Russian Ministry of Digital Development. For development:

- **Production setup**: Download the "Russian Trusted Root CA" certificate from [Gosuslugi](https://www.gosuslugi.ru/crt) and configure:
  ```bash
  export GIGACHAT_CA_BUNDLE_FILE="/path/to/Russian_Trusted_Root_CA.crt"
  ```

- **Development only** (not recommended): Disable SSL verification:
  ```bash
  export GIGACHAT_VERIFY_SSL_CERTS=false
  ```

5. **Verify installation**

```bash
make all  # Run linting, type checking, and tests
```

If all checks pass, you're ready to start contributing! 🚀

### Quick Reference: Make Commands

```bash
make help              # Display all available commands
make install           # Install dependencies and pre-commit hooks
make fmt               # Auto-format code with Ruff
make lint              # Check code style
make mypy              # Run type checking
make test              # Run unit tests with coverage
make test-integration  # Run integration tests (requires credentials)
make all               # Run full CI suite (lint + mypy + test)
make clean             # Remove build artifacts and caches
```

## Development Workflow

### Branching Strategy

We follow a fork-and-pull-request model:

1. **Fork the repository** to your GitHub account
2. **Clone your fork** locally
3. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

### Branch Naming Conventions

Use descriptive branch names with prefixes:

- `feature/` — New features (e.g., `feature/add-streaming-timeout`)
- `fix/` — Bug fixes (e.g., `fix/handle-empty-response`)
- `docs/` — Documentation updates (e.g., `docs/update-auth-guide`)
- `refactor/` — Code refactoring (e.g., `refactor/simplify-retry-logic`)
- `test/` — Test improvements (e.g., `test/add-embeddings-coverage`)

### Making Changes

1. **Make your changes** in your feature branch
2. **Follow code quality standards** (see [Code Quality Standards](#code-quality-standards))
3. **Add or update tests** to cover your changes
4. **Update documentation** if needed (docstrings, README, examples)
5. **Run quality checks** before committing:
   ```bash
   make fmt   # Auto-format your code
   make all   # Run all checks (lint + mypy + test)
   ```

6. **Commit your changes** with clear commit messages (see [Commit Message Guidelines](#commit-message-guidelines))

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit` to ensure code quality:

- **Ruff**: Formatting and linting
- **mypy**: Type checking
- **Standard checks**: Trailing whitespace, YAML validation, etc.

If pre-commit fails, fix the issues and commit again. To manually run pre-commit on all files:

```bash
make pre  # Or: pre-commit run --all-files
```

### Keeping Your Fork Updated

Regularly sync your fork with the upstream repository:

```bash
# Add upstream remote (one-time setup)
git remote add upstream https://github.com/ai-forever/gigachat.git

# Fetch and merge upstream changes
git fetch upstream
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

### Submitting Your Changes

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a pull request** on GitHub from your fork to `ai-forever/gigachat:main`

3. **Fill out the PR template** with all required information

4. **Wait for review** — maintainers will review your PR and may request changes

5. **Address feedback** by making additional commits to your branch

6. **Keep your PR updated** by rebasing on the latest `main` if needed

> **Note**: For detailed guidance on the pull request process, see the [Pull Request Process](#pull-request-process) section below.

## Code Quality Standards

We maintain high code quality standards to ensure consistency and maintainability. All contributions must adhere to the following guidelines.

### Code Style

- **PEP 8 Compliance**: Follow [PEP 8](https://pep.python.org/pep-0008/) style guidelines
- **Line Length**: Maximum 120 characters (configured in `pyproject.toml`)
- **Formatting**: Use Ruff for automatic formatting
- **Linting**: Pass all Ruff linting checks

Run these commands to check and fix style issues:

```bash
make fmt   # Auto-format code
make lint  # Check for style issues
```

### Type Hints

- **Required**: All functions and methods must have type hints
- **Strict Mode**: We use mypy in strict mode
- **Python 3.8 Compatibility**: Use `Type[...]` instead of `type[...]` for generic types
- **Return Types**: Always specify return types, including `None`

Example:

```python
from typing import Optional, List

def process_messages(
    messages: List[str],
    max_tokens: Optional[int] = None,
) -> List[str]:
    """Process a list of messages."""
    return [msg.strip() for msg in messages]
```

Run type checking:

```bash
make mypy
```

### Docstrings

All public modules, classes, functions, and methods must have docstrings following Google style.

**Key Requirements:**

- **Style**: Google Python Style Guide
- **Mood**: Imperative (e.g., "Return the result" not "Returns the result")
- **Language**: English only
- **Type Information**: In function signatures, not docstrings (we use type hints)

**Standard Style (Minimal Docstrings):**

Most functions in the codebase use minimal, one-line docstrings:

```python
def chat_sync(
    client: httpx.Client,
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> ChatCompletion:
    """Return a model response based on the provided messages."""
    # Implementation here
```

```python
def get_embeddings(
    texts: List[str],
    model: str = "GigaChat-Embeddings",
) -> List[List[float]]:
    """Generate embeddings for a list of texts."""
    # Implementation here
```

Type hints provide parameter information, so `Args:` sections are typically not needed.

**Optional: Extended Docstrings for Complex APIs**

For complex public APIs, you may optionally add `Args:` section:

```python
def complex_method(
    self,
    param1: str,
    param2: Optional[int] = None,
) -> Result:
    """Perform a complex operation.

    Args:
        param1: Description of first parameter.
        param2: Description of optional parameter.
    """
    # Implementation
```

However, most functions use only the one-line summary.

### Code Organization

- **Imports**: Organized by Ruff (stdlib → third-party → local)
- **Module Structure**: Follow existing patterns in the codebase
- **Single Responsibility**: Keep functions and classes focused
- **DRY Principle**: Don't repeat yourself — extract common logic

### Comments

- **Minimize Comments**: Write self-documenting code with clear names
- **When to Comment**: Explain "why" not "what" for complex logic
- **TODO Comments**: Use `# TODO:` for temporary notes (but prefer issues)
- **No Commented Code**: Remove unused code instead of commenting it out

### Automated Checks

All code must pass these automated checks:

```bash
make all  # Run all checks together
```

Or individually:

```bash
make fmt    # Auto-format with Ruff
make lint   # Ruff linting
make mypy   # Type checking
make test   # Unit tests
```

These checks also run automatically via pre-commit hooks and in CI.

### Python Version Compatibility

- **Supported Versions**: Python 3.8 through 3.13
- **Compatibility Notes**:
  - Use `Type[X]` not `type[X]` (Python 3.8 doesn't support lowercase)
  - Use `Dict`, `List`, `Optional` from `typing` (not builtin types as generics)
  - Test on multiple Python versions when possible

### Dependencies

- **Minimal Dependencies**: Only add dependencies when absolutely necessary
- **Justification Required**: Explain why a new dependency is needed
- **Version Constraints**: Use compatible ranges (e.g., `>=2.0,<3`)
- **Update Lockfile**: Run `uv lock` after changing dependencies

## Testing

We maintain comprehensive test coverage with both unit and integration tests. All new code must include appropriate tests.

### Test Types

#### Unit Tests

Located in `tests/unit/`, unit tests verify internal logic using mocked HTTP responses:

- **Purpose**: Test logic, error handling, and edge cases
- **Mocking**: Uses `pytest-httpx` to mock HTTP requests
- **Speed**: Fast execution (entire suite runs in seconds)
- **Coverage**: Aim for high coverage (90%+) on new code

#### Integration Tests

Located in `tests/integration/`, integration tests verify real API interactions using VCR cassettes:

- **Purpose**: Validate API response parsing and Pydantic models
- **VCR Cassettes**: Record real HTTP interactions once, replay deterministically
- **Speed**: Fast replay (~0.1s), no network calls needed
- **Credentials**: Optional for contributors (cassettes are committed)

### Running Tests

```bash
# Run all unit tests (default, includes coverage)
make test

# Run integration tests (requires credentials or uses cassettes)
make test-integration

# Run specific test file
uv run pytest tests/unit/gigachat/test_client_chat.py

# Run specific test function
uv run pytest tests/unit/gigachat/test_client_chat.py::test_chat_completion

# Run with verbose output
uv run pytest -v

# Run tests matching a pattern
uv run pytest -k "test_retry"
```

### Writing Unit Tests

Unit tests should follow these patterns:

**Example: Testing a sync method**

```python
import pytest
from pytest_httpx import HTTPXMock
from gigachat import GigaChat
from gigachat.models import ChatCompletion

def test_chat_completion(httpx_mock: HTTPXMock) -> None:
    """Test basic chat completion."""
    # Mock the response
    httpx_mock.add_response(
        method="POST",
        url="https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        json={
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Hello!"},
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            "model": "GigaChat",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        },
    )

    # Test the method
    with GigaChat(credentials="test", verify_ssl_certs=False) as client:
        result = client.chat("Hello")
        assert isinstance(result, ChatCompletion)
        assert result.choices[0].message.content == "Hello!"
```

**Example: Testing an async method**

```python
async def test_achat_completion(httpx_mock: HTTPXMock) -> None:
    """Test async chat completion."""
    httpx_mock.add_response(
        method="POST",
        url="https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        json={"choices": [{"message": {"role": "assistant", "content": "Hi!"}}]},
    )

    async with GigaChat(credentials="test", verify_ssl_certs=False) as client:
        result = await client.achat("Hello")
        assert result.choices[0].message.content == "Hi!"
```

### Writing Integration Tests

Integration tests use VCR to record and replay HTTP interactions:

**Example: Integration test**

```python
import pytest
from gigachat import GigaChat, ChatCompletion

@pytest.mark.integration
@pytest.mark.vcr
def test_chat_integration(gigachat_client: GigaChat) -> None:
    """Test chat completion with real API."""
    result = gigachat_client.chat("Say hello")
    assert isinstance(result, ChatCompletion)
    assert result.choices is not None
    assert len(result.choices) > 0
```

**Recording new cassettes:**

1. Ensure `.env` has valid credentials
2. Run the test: `pytest -m integration tests/integration/test_your_test.py`
3. Cassette is created in `tests/integration/cassettes/`
4. Review for sensitive data, then commit

### Test Organization

Tests should be organized by the module they're testing:

```
tests/
├── unit/
│   ├── gigachat/
│   │   ├── test_client_chat.py      # Chat methods
│   │   ├── test_client_files.py     # File operations
│   │   ├── test_client_tools.py     # Utility methods
│   │   ├── test_exceptions.py       # Exception handling
│   │   └── api/
│   │       ├── test_chat.py         # API layer tests
│   │       └── ...
│   └── conftest.py                  # Shared fixtures
└── integration/
    ├── test_chat_vcr.py             # Chat API integration
    ├── test_models_vcr.py           # Models API integration
    └── cassettes/                   # Recorded HTTP interactions
```

### Test Coverage

- **Target**: Aim for high coverage (90%+) on new code
- **Check Coverage**: Run `make test` to see coverage report
- **Focus Areas**:
  - Happy path (normal operation)
  - Error cases (exceptions, validation)
  - Edge cases (empty inputs, boundaries)
  - Both sync and async variants

### Test Fixtures

Common fixtures are available in `tests/unit/conftest.py`:

- `httpx_mock`: Mock HTTP requests (pytest-httpx)
- `base_url`: Standard API base URL
- `auth_url`: OAuth authentication URL
- `credentials`: Test credentials

For integration tests, use fixtures from `tests/integration/conftest.py`:

- `gigachat_client`: Configured sync client
- `gigachat_async_client`: Configured async client

### Continuous Integration

Tests run automatically in CI on:

- All Python versions (3.8-3.13) for unit tests
- Python 3.12 only for integration tests (cassettes are Python-agnostic)

Ensure all tests pass locally before submitting your PR:

```bash
make all  # Runs lint + mypy + test
```

## Commit Message Guidelines

Clear and consistent commit messages help maintain a readable project history and make it easier to understand changes.

### Format

Use the conventional commits format:

```
<type>: <subject>

[optional body]

[optional footer]
```

### Type

The type describes the kind of change:

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring (no functional change)
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependency updates, build config

### Subject

- Use imperative mood: "Add feature" not "Added feature" or "Adds feature"
- Keep it short (50 characters or less)
- Don't end with a period
- Capitalize the first letter

### Body (Optional)

- Provide context for the change
- Explain "why" not "what" (the diff shows what changed)
- Wrap at 72 characters
- Separate from subject with a blank line

### Footer (Optional)

- Reference issues: `Closes #123` or `Fixes #456`
- Note breaking changes: `BREAKING CHANGE: description`

### Examples

**Good commit messages:**

```
feat: add retry mechanism for rate-limited requests

Implement exponential backoff with configurable max retries.
Handles 429 status codes and Retry-After headers.

Closes #45
```

```
fix: handle SSE chunks without space after colon

Some servers send "data:{...}" instead of "data: {...}".
Updated parse_chunk() to strip leading whitespace from values.
```

```
docs: update SSL certificate installation guide

Add troubleshooting section for common certificate errors
on Windows and macOS.
```

```
test: add integration tests for embeddings endpoint

Uses VCR cassettes to record real API interactions.
Covers both sync and async variants.
```

**Bad commit messages:**

```
update stuff          # Too vague
Fixed a bug.          # Not imperative, no context
WIP                   # Not descriptive
```

### Multiple Changes

If your commit includes multiple unrelated changes, consider splitting it into separate commits:

```bash
# Stage and commit changes separately
git add src/gigachat/client.py
git commit -m "feat: add timeout parameter to chat method"

git add tests/unit/gigachat/test_client_chat.py
git commit -m "test: add tests for chat timeout"
```

### Amending Commits

If you need to fix your last commit:

```bash
# Modify files
git add .
git commit --amend

# Or just update the message
git commit --amend -m "new message"
```

> **Note**: Don't amend commits that have already been pushed to a shared branch (like an open PR after review has started).

## Pull Request Process

Follow these steps to submit a high-quality pull request that will be reviewed and merged quickly.

### Before Submitting

Ensure your pull request is ready by completing these steps:

1. **Run all quality checks**
   ```bash
   make all  # Runs lint, mypy, and tests
   ```

2. **Add tests** for new functionality or bug fixes

3. **Update documentation**
   - Add/update docstrings for new code
   - Update README.md if adding user-facing features
   - Add examples if helpful

4. **Review your own changes**
   ```bash
   git diff main...your-branch
   ```

5. **Rebase on latest main** (if needed)
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

6. **Clean up your commits**
   - Use clear commit messages
   - Squash "fix typo" or "WIP" commits if appropriate
   - Ensure each commit builds and passes tests

### Submitting Your PR

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a pull request** on GitHub
   - Go to https://github.com/ai-forever/gigachat
   - Click "New Pull Request"
   - Select your fork and branch

3. **Fill out the PR template** completely:
   - **Description**: Clear explanation of what and why
   - **Type of Change**: Check appropriate boxes
   - **Changes Made**: List key changes
   - **Testing**: Describe how you tested
   - **Checklist**: Verify all items

4. **Link related issues** using keywords:
   - `Closes #123`
   - `Fixes #456`
   - `Relates to #789`

### PR Title Guidelines

Use the same format as commit messages:

```
feat: add timeout parameter to chat method
fix: handle empty response in stream mode
docs: improve authentication examples
```

### During Review

**What to expect:**

- Maintainers will review your PR within a few days
- You may receive feedback or requests for changes
- CI checks must pass before merging

**Responding to feedback:**

1. **Read feedback carefully** and ask questions if unclear

2. **Make requested changes** in new commits (don't force-push during active review)
   ```bash
   # Make changes
   git add .
   git commit -m "address review feedback"
   git push origin feature/your-feature-name
   ```

3. **Reply to comments** when changes are made
   - Mark conversations as resolved when addressed
   - Explain your reasoning if you disagree with feedback

4. **Re-request review** after addressing all feedback

### CI Checks

Your PR must pass all CI checks:

- ✅ **Linting**: Code follows style guidelines
- ✅ **Type Checking**: mypy passes in strict mode
- ✅ **Tests**: All tests pass on Python 3.8-3.13
- ✅ **Integration Tests**: VCR cassette tests pass

If CI fails:
1. Check the error logs in GitHub Actions
2. Fix issues locally
3. Push fixes to your branch
4. CI will re-run automatically

### Common Rejection Reasons

PRs may be rejected or require significant changes if:

- Missing tests for new functionality
- Breaking changes without discussion
- Doesn't follow code quality standards
- Adds unnecessary dependencies
- Scope is too large (consider breaking into smaller PRs)
- Conflicts with project direction or roadmap

### After Approval

Once your PR is approved:

1. **Squash commits if requested** by maintainers
2. **Wait for merge** — maintainers will merge when ready
3. **Delete your branch** after merge (optional)
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

### Tips for Faster Review

- **Keep PRs focused** — one feature or fix per PR
- **Keep PRs small** — easier to review, faster to merge
- **Write good descriptions** — help reviewers understand context
- **Respond promptly** to feedback
- **Be patient and courteous** — maintainers are volunteers

### Draft PRs

Use draft PRs for work in progress:

1. Open PR as "Draft"
2. Get early feedback on approach
3. Mark "Ready for review" when complete

This is helpful for large features or when you want input before finishing.

## Issue Reporting

High-quality issue reports help us understand and fix problems quickly. Please follow these guidelines when reporting issues.

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
   - Check both open and closed issues
   - Use GitHub search with relevant keywords

2. **Check the documentation**
   - [README.md](README.md) for usage examples
   - [Official API documentation](https://developers.sber.ru/docs/ru/gigachat/api/main)
   - Code examples in [examples/](examples/)

3. **Verify it's actually a bug**
   - Test with the latest version: `pip install --upgrade gigachat`
   - Try with minimal code to isolate the issue
   - Check if it's a configuration problem (SSL certificates, credentials)

### Bug Reports

Use the bug report template when creating a bug report. Include:

**Required Information:**

- **Clear description** of the bug
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Minimal code example** that reproduces the bug
- **GigaChat version**: `pip show gigachat`
- **Python version**: `python --version`
- **Operating system**: Linux, macOS, or Windows
- **Error messages** and stack traces (full output)

**Good Bug Report Example:**

```markdown
## Description
`client.stream()` raises `AttributeError` when server returns empty response

## Steps to Reproduce
1. Install gigachat 0.2.0
2. Run the following code:
   ```python
   from gigachat import GigaChat

   with GigaChat() as client:
       for chunk in client.stream("Hello"):
           print(chunk)
   ```
3. Server returns empty response

## Expected Behavior
Should handle empty responses gracefully or provide clear error message

## Actual Behavior
Raises AttributeError: 'NoneType' object has no attribute 'choices'

## Environment
- gigachat: 0.2.0
- Python: 3.11.5
- OS: Ubuntu 22.04
- Error: [full stack trace]
```

**Bad Bug Report Example:**

```markdown
Doesn't work

I tried to use streaming but got an error. Can you fix it?
```

### Feature Requests

Use the feature request template to propose new features. Include:

- **Problem statement**: What problem does this solve?
- **Proposed solution**: How should it work?
- **API design** (optional): Example code showing proposed usage
- **Use case**: Why is this useful?
- **Alternatives considered**: Other approaches you've tried

**Tips for feature requests:**

- Explain the "why" behind the feature
- Consider if it fits the project scope
- Be open to alternative implementations
- Indicate if you're willing to contribute the implementation

### Questions

For questions about usage, please use:

- **GitHub Discussions** for general questions
- Check existing issues for similar questions

Don't create issues for questions like:
- "How do I use feature X?"
- "What's the best way to do Y?"
- "Is this the right approach?"

### Issue Labels

Maintainers will label your issue to help organize and prioritize:

- `bug` — Something isn't working
- `enhancement` — New feature or request
- `documentation` — Improvements or additions to documentation
- `good first issue` — Good for newcomers
- `help wanted` — Extra attention needed
- `question` — Further information requested
- `wontfix` — This will not be worked on
- `duplicate` — Duplicate of another issue

### Security Issues

**Do not report security vulnerabilities in public issues.**

For security issues, please report privately through GitHub's security advisory feature or contact the maintainers directly.

### Issue Etiquette

- **Be respectful and constructive**
- **Provide complete information** the first time
- **Respond to questions** from maintainers
- **Update the issue** if you find new information
- **Close the issue** if you solve it yourself (and share the solution!)
- **Don't bump issues** with "+1" comments (use 👍 reactions instead)

### What Happens Next

After you submit an issue:

1. **Maintainers will review** within a few days
2. **You may be asked for more information**
3. **Issue may be labeled** and prioritized
4. **Fix timeline depends on** severity, complexity, and maintainer availability

Thank you for helping improve GigaChat! 🙏

## Documentation Guidelines

Clear documentation helps users understand and effectively use the SDK.

### Code Documentation

All public functions, classes, and modules must have docstrings. For detailed requirements and examples, see the [Docstrings](#docstrings) section under **Code Quality Standards**.

**Quick Summary:**
- Use minimal, imperative-mood docstrings (e.g., "Return..." not "Returns...")
- One-line summary is typically sufficient
- Type hints in signatures replace parameter documentation
- Optional `Args:` sections for complex public APIs

### README and Examples

When adding user-facing features:

1. **Add usage examples** to README.md if the feature is common
2. **Create example files** in `examples/` for complex features
3. **Keep examples working** — test them before committing
4. **Show both sync and async** variants when applicable

### Code Comments

- **Prefer self-documenting code** over comments
- **Comment "why" not "what"** — the code shows what it does
- **No commented-out code** — delete it instead (Git preserves history)

Example of good vs bad comments:

```python
# Bad: Explains what (obvious from code)
# Loop through messages and process them
for msg in messages:
    process(msg)

# Good: Explains why (not obvious)
# Force refresh token before batch operation to avoid mid-batch auth failures
self._refresh_token()
for msg in messages:
    process(msg)
```

## Project Architecture

Understanding the project structure will help you navigate the codebase and make contributions effectively.

### Directory Structure

The project follows a layered architecture:

**Source Code (`src/gigachat/`):**
- **Client layer**: Main client classes (sync, async, hybrid)
- **API layer** (`api/`): Low-level HTTP functions, one module per endpoint group
- **Models layer** (`models/`): Pydantic V2 request/response models
- **Cross-cutting concerns**: Authentication, retry, exceptions, settings, context

**Tests (`tests/`):**
- **Unit tests** (`unit/`): Mocked HTTP tests using pytest-httpx
- **Integration tests** (`integration/`): VCR cassette-based tests with real API responses

**Other:**
- **Examples** (`examples/`): Working code samples for users
- **Configuration**: `pyproject.toml` for dependencies and tooling

**Navigation tip:** Use your IDE's "Go to Definition" or search functionality to explore the codebase. The structure is intuitive — if you're looking for chat-related code, check `api/chat.py` and `models/chat.py`.

### Key Components

#### Client Layer

- **`GigaChat`**: Hybrid client (inherits from both sync and async)
- **`GigaChatSyncClient`**: Synchronous HTTP client
- **`GigaChatAsyncClient`**: Asynchronous HTTP client
- **`_BaseClient`**: Shared configuration and initialization

All three clients support the same methods with sync/async variants.

#### API Layer (`src/gigachat/api/`)

Low-level functions that handle HTTP requests:
- One module per API endpoint group
- Functions accept `httpx.Client`/`AsyncClient` and return Pydantic models
- Decorated with `@_with_auth`, `@_with_retry` for cross-cutting concerns

#### Models Layer (`src/gigachat/models/`)

Pydantic V2 models for all API requests and responses:
- **Request models**: `Chat`, `Messages`, `Function`, etc.
- **Response models**: `ChatCompletion`, `Embeddings`, `Model`, etc.
- **Base class**: `APIResponse` (includes `x_headers` for metadata)

#### Authentication

- **Decorators**: `@_with_auth`, `@_awith_auth` (request-response)
- **Stream decorators**: `@_with_auth_stream`, `@_awith_auth_stream`
- **Auto-refresh**: Tokens refreshed on 401 errors
- **Context var support**: `authorization_cvar` for manual token management

#### Retry Mechanism

- **Decorators**: `@_with_retry`, `@_awith_retry` (request-response)
- **Stream decorators**: `@_with_retry_stream`, `@_awith_retry_stream`
- **Exponential backoff**: Configurable via `max_retries`, `retry_backoff_factor`
- **Respects Retry-After**: Honors server retry hints

### Design Patterns

#### Decorator Stacking

Methods use multiple decorators for separation of concerns:

```python
@_with_retry
@_with_auth
def chat(self, chat: Chat) -> ChatCompletion:
    return chat.chat_sync(self._client, chat=chat)
```

Order matters: retry wraps auth, so auth errors trigger retries.

#### Lazy Initialization

HTTP clients are created on first use, not in `__init__`. This prevents resource leaks when clients are instantiated but never used (e.g., when only async methods are called on the hybrid `GigaChat` class).

#### Context Variables

Thread-safe context variables for request-specific data:

```python
from gigachat import session_id_cvar

session_id_cvar.set("my-session-123")
# All requests in this context will include X-Session-ID header
```

### Adding New Features

When adding a new API endpoint:

1. **Add Pydantic models** in `src/gigachat/models/`
2. **Add API functions** in `src/gigachat/api/`
3. **Add client methods** in `src/gigachat/client.py`
4. **Export in `__init__.py`** if user-facing
5. **Add tests** in `tests/unit/gigachat/`
6. **Add integration tests** in `tests/integration/` (optional)

### Dependencies

- **httpx**: HTTP client (sync + async)
- **pydantic**: Data validation and serialization (V2)
- **pydantic-settings**: Configuration management

Keep dependencies minimal — only add if absolutely necessary.

## License

By contributing to GigaChat, you agree that your contributions will be licensed under the MIT License.

This means:
- Your code will be freely available to everyone
- Others can use, modify, and distribute your contributions
- You retain copyright to your contributions
- You grant others permission to use your work under the MIT License terms

The full license text is available in the [LICENSE](LICENSE) file in the repository root.

### Contributor Rights

When you submit a pull request, you are:
- Confirming you have the right to contribute the code
- Granting the project maintainers and users the right to use your contribution
- Agreeing that your contribution is provided "as is" without warranties

If you're contributing on behalf of your employer, ensure you have permission to contribute under these terms.

---

Thank you for contributing to GigaChat! Your efforts help make this project better for everyone. 🚀
