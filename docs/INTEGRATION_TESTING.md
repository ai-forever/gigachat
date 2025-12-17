# Integration Testing Guide

This guide covers the VCR/cassette-based integration testing setup for the GigaChat SDK.

## Overview

Integration tests use [VCR.py](https://vcrpy.readthedocs.io/) via `pytest-recording` to record real HTTP interactions and replay them deterministically. This provides:

- **Real API validation**: Tests actual response parsing and Pydantic model validation
- **Fast execution**: No network calls during replay (~0.1s vs ~11s)
- **Deterministic CI**: Cassettes committed to repo, no credentials needed in CI
- **Schema drift detection**: Cassette mismatches catch API changes

## Directory Structure

```
tests/
├── integration/
│   ├── __init__.py
│   ├── conftest.py            # VCR config, fixtures, credential scrubbing
│   ├── cassettes/             # Recorded HTTP interactions (YAML)
│   │   ├── test_chat_simple.yaml
│   │   ├── test_stream_simple.yaml
│   │   ├── test_get_models.yaml
│   │   └── ...
│   ├── test_chat_vcr.py       # /chat/completions endpoint tests
│   ├── test_models_vcr.py     # /models endpoint tests
│   ├── test_tokens_vcr.py     # /tokens/count endpoint tests
│   └── test_embeddings_vcr.py # /embeddings endpoint tests
└── unit/                      # Mocked unit tests (pytest-httpx)
```

## Setup

### Dependencies

Integration testing requires these dev dependencies (already in `pyproject.toml`):
- `vcrpy>=6.0.0`
- `pytest-recording>=0.13.0`
- `python-dotenv>=1.0.0`

### Environment Variables

Create a `.env` file in the project root (gitignored):

```bash
GIGACHAT_CREDENTIALS=your_oauth_credentials_here
GIGACHAT_SCOPE=GIGACHAT_API_PERS  # or GIGACHAT_API_CORP
```

See `.env.example` for reference.

## Running Tests

### Unit Tests Only (Default)

```bash
uv run pytest                    # Runs only unit tests (356 tests)
make test                        # Same via Makefile
```

### Integration Tests Only

```bash
uv run pytest -m integration     # Runs only integration tests
make test-integration            # Same via Makefile
```

### Integration Tests (CI Mode)

```bash
uv run pytest -m integration --record-mode=none  # Replay only, no recording
make test-integration-ci                          # Same via Makefile
```

### All Tests

```bash
uv run pytest -m ""              # Runs all tests (unit + integration)
```

## Recording Modes

VCR supports different recording modes controlled by `--record-mode`:

| Mode | Use Case | Command |
|------|----------|---------|
| `once` | Default — record if cassette doesn't exist | `make test-integration` |
| `none` | CI — replay only, fail if cassette missing | `make test-integration-ci` |
| `all` | Update all cassettes | `pytest -m integration --record-mode=all` |
| `new_episodes` | Add new interactions to existing cassettes | `pytest -m integration --record-mode=new_episodes` |

### Recording New Cassettes

1. Ensure `.env` has valid credentials
2. Run: `pytest -m integration tests/integration/test_your_test.py`
3. Cassette is created in `tests/integration/cassettes/`
4. Review YAML file for any sensitive data leakage
5. Commit the cassette

### Updating Stale Cassettes

```bash
pytest -m integration --record-mode=all
```

## CI/CD Integration

Integration tests run automatically in GitHub Actions CI pipeline.

### How It Works

1. **Separate CI job**: Integration tests run in a dedicated `integration-test` job
2. **Single Python version**: Tests run on Python 3.12 only (cassettes are Python-agnostic)
3. **Replay mode**: Uses `--record-mode=none` to ensure only cassette replay, no network calls
4. **No credentials needed**: Dummy credentials are used automatically in CI (detected via `CI` env var)

### CI Configuration

From `.github/workflows/gigachat.yml`:

```yaml
integration-test:
  name: Integration Tests
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v5
    - run: uv python install 3.12
    - run: uv sync --all-extras --dev
    - run: uv run pytest -m integration --record-mode=none
```

### Why Single Python Version?

VCR cassettes contain raw HTTP responses which are Python-agnostic. The tests verify:
- API response parsing (JSON)
- Pydantic model validation
- HTTP client behavior (httpx)

None of these vary by Python version. Unit tests (which run on all Python versions) cover internal logic where version differences could matter.

### Credential Handling in CI

The `_get_credentials()` function in `conftest.py` automatically detects CI:

```python
if credentials:
    return credentials, scope

if os.getenv("CI"):  # GitHub Actions sets CI=true
    return "dummy-credentials-for-vcr-replay", scope

pytest.skip("GIGACHAT_CREDENTIALS not set (and not in CI)")
```

This means:
- **Local with credentials**: Uses real credentials (can record new cassettes)
- **Local without credentials**: Tests are skipped
- **CI**: Uses dummy credentials (VCR handles all HTTP via cassettes)

### Adding New Tests for CI

When adding new integration tests:

1. Record cassette locally with real credentials
2. Commit the cassette file to `tests/integration/cassettes/`
3. CI will automatically replay the cassette

If you forget to commit a cassette, CI will fail with "cassette not found" error.

## Security: Credential Scrubbing

The `conftest.py` automatically scrubs sensitive data from cassettes:

### Request Scrubbing (`_scrub_request`)
- Replaces `scope=XXX` with `scope=REDACTED` in OAuth request bodies

### Response Scrubbing (`_scrub_response`)
- Replaces `access_token` values with `"REDACTED"`
- Replaces `tok` values with `"REDACTED"`
- Replaces `expires_at` with year 2100 timestamp (prevents token expiration during replay)

### Header Filtering
- `Authorization: Bearer XXX` → `Authorization: Bearer REDACTED`

**Always review cassettes before committing** to ensure no credentials leaked.

## Writing New Integration Tests

### Basic Test Structure

```python
import pytest
from gigachat import GigaChat, ChatCompletion

@pytest.mark.integration
@pytest.mark.vcr
def test_chat_completion(gigachat_client: GigaChat) -> None:
    """Test chat completion endpoint."""
    from gigachat import Chat, Messages, MessagesRole

    chat = Chat(
        messages=[Messages(role=MessagesRole.USER, content="Hello!")]
    )
    result = gigachat_client.chat(chat)

    assert isinstance(result, ChatCompletion)
    assert result.choices is not None
```

### Async Tests

```python
@pytest.mark.integration
@pytest.mark.vcr
async def test_async_chat(gigachat_async_client: GigaChat) -> None:
    """Test async chat completion."""
    result = await gigachat_async_client.achat(chat)
    assert isinstance(result, ChatCompletion)
```

### Error Case Tests

```python
@pytest.mark.integration
@pytest.mark.vcr
def test_model_not_found(gigachat_client: GigaChat) -> None:
    """Test 404 error handling."""
    with pytest.raises(NotFoundError) as exc_info:
        gigachat_client.get_model("NonExistentModel")

    assert exc_info.value.status_code == 404
```

### Key Points

1. **Always use both markers**: `@pytest.mark.integration` and `@pytest.mark.vcr`
2. **Use provided fixtures**: `gigachat_client` (sync) or `gigachat_async_client` (async)
3. **Test realistic scenarios**: Happy paths, error cases, edge cases
4. **Cassette per test**: Each test function gets its own cassette file

## Troubleshooting

### "Cassette not found" in CI
- Ensure cassette was committed to repo
- Check cassette filename matches test function name

### "Request not in cassette"
- API behavior changed — re-record with `--record-mode=all`
- Test modified to make different request — re-record

### Token Expiration Errors During Replay
- Response scrubbing should set `expires_at` to year 2100
- Check `_scrub_response` in `conftest.py` is working

### "GIGACHAT_CREDENTIALS not set" (local)
- Create `.env` file with credentials
- Or export environment variable: `export GIGACHAT_CREDENTIALS=...`
- Note: In CI, dummy credentials are used automatically

## VCR Configuration Reference

From `tests/integration/conftest.py`:

```python
@pytest.fixture(scope="module")
def vcr_config() -> Dict[str, Any]:
    return {
        "filter_headers": [
            ("authorization", "Bearer REDACTED"),
        ],
        "match_on": ["method", "scheme", "host", "port", "path", "query", "body"],
        "record_mode": "once",
        "decode_compressed_response": True,
        "before_record_request": _scrub_request,
        "before_record_response": _scrub_response,
    }
```

**Note**: The `"body"` matcher ensures POST requests with different payloads (e.g., different inputs to `/tokens/count`) are matched to their respective cassettes.

## Implementation Progress

This section tracks which API endpoints have integration test coverage.

### Completed

- [x] `/chat/completions` — Chat completions and streaming (6 tests)
  - `test_chat_simple` — Basic chat completion (sync)
  - `test_achat_simple` — Basic chat completion (async)
  - `test_stream_simple` — Streaming chat completion (sync)
  - `test_astream_simple` — Streaming chat completion (async)
  - `test_chat_model_not_found` — 404 error handling (sync)
  - `test_achat_model_not_found` — 404 error handling (async)
- [x] `/models` — List and get models (6 tests)
  - `test_get_models` — List all available models (sync)
  - `test_get_model` — Get specific model by name (sync)
  - `test_get_model_not_found` — 404 error handling (sync)
  - `test_aget_models` — List all available models (async)
  - `test_aget_model` — Get specific model by name (async)
  - `test_aget_model_not_found` — 404 error handling (async)
- [x] `/tokens/count` — Count tokens in text (4 tests)
  - `test_tokens_count_single` — Single text (sync)
  - `test_tokens_count_multiple` — Batch of texts (sync)
  - `test_atokens_count_single` — Single text (async)
  - `test_atokens_count_multiple` — Batch of texts (async)
- [x] `/embeddings` — Generate text embeddings (4 tests)
  - `test_embeddings_single` — Single text (sync)
  - `test_embeddings_multiple` — Batch of texts (sync)
  - `test_aembeddings_single` — Single text (async)
  - `test_aembeddings_multiple` — Batch of texts (async)

## Related Documentation

- `docs/REFACTORING.md` — Historical context on why VCR was chosen
