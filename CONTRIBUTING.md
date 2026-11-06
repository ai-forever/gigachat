# Contributing to GigaChat

Use Python 3.10 or newer and uv. Changes should preserve the supported public API, carry focused regression coverage, and explain any compatibility change in [MIGRATION.md](MIGRATION.md).

## Setup and checks

```bash
uv sync --group dev
uv run pre-commit install
make lint
make ty
make test
make test-integration
```

`make all` runs lint, ty with warnings treated as errors, and the unit suite. `make fmt` runs Ruff formatting and autofixes. `make test-integration` replays existing cassettes with network access blocked; it needs no live credentials. Install optional dependencies with `uv sync --group dev --extra aiohttp` when working on the aiohttp adapter. Other extras are `http2` and `socks` for native HTTPX2. Install the live notebook tooling separately with `uv sync --group notebook`.

Use `uv run pytest tests/unit/gigachat/test_streaming_030.py` for focused stream, raw response, and download tests. Local transport tests use loopback servers to check sockets, connection pools, cancellation, and TLS. These checks are different from mocked request-policy tests and live API execution.

Do not record over cassettes or issue live requests as a side effect of replay. A new live or recording workflow must be explicit, use isolated credentials, and remove secrets from any resulting artifacts. Copy `.env.example` for local configuration; never commit credentials.

## Style and architecture

Use modern Python 3.10 type syntax (`dict[str, Any]`, `T | None`), native Pydantic V2, Ruff's configured 120-character line length, and ty with warnings treated as errors. Keep docstrings concise and imperative. Commit messages use conventional prefixes such as `fix:`, `feat:`, and `test:`. Pre-commit failures should be fixed before committing.

The API modules under `src/gigachat/api/` own endpoint-specific request builders. Shared execution belongs in `_core/execution.py`; avoid endpoint-specific retry loops. `_core/request.py` owns immutable options, headers, replay primitives, and transport-neutral timeout conversion. `_core/response.py` owns status mapping, response parsing, and raw/byte wrappers; `_core/streaming.py` owns SSE decoding and stream lifecycle. `_core/http_client.py` owns HTTPX2 and TLS setup, with the optional adapter under `_vendor/httpx_aiohttp/`. `_core/base_client.py` owns configuration and owner/view state. Core modules never import API, resources, or public clients at runtime. Chat and file operations belong in `resources/`; the public client delegates to them. Keep HTTPX2 types at transport boundaries and never install a global HTTPX alias.

Stateful clients and lightweight option views share ownership and token state. Closing a view invalidates only that view. A hybrid owner's close() closes its sync side; awaited aclose() closes both sides. Async clients/views must remain on their initial event loop. Preserve the constructor `None` compatibility rules, ContextVar precedence, and caller-owned client/session lifetime. Never retry after yielding partial output. Every intermediary async generator must explicitly close the iterator it owns on early exit. Do not log prompts, credentials, OAuth bodies, raw chunks, or file content.

When adding an endpoint:

1. Add request/response models under `models/` with the existing alias and schema behavior.
2. Build sync/async API functions using the common executor.
3. Add high-level methods with RequestOptions support and appropriate typed lifecycle wrappers.
4. Export public names and document observable behavior.
5. Cover HTTP shape, errors, metadata, cancellation/cleanup, and input immutability where applicable.

## Tests and dependencies

Use `httpx2.MockTransport`, or `HTTPXMock` from `tests.httpx_mock`; do not import the legacy `pytest_httpx.HTTPXMock`. Both sync and async requests should be exercised. `asyncio_mode="auto"` handles async pytest tests without redundant markers.

Cassette replay uses the YAML files under `tests/integration/cassettes/` through the repository's HTTPX2 adapter. Tests are marked `integration` and excluded from normal unit runs. Their historical `vcr` markers do not authorize recording or live access. Socket tests should bind loopback only, use temporary certificates/files, and report exactly which backend and interpreter were exercised.

Keep core dependencies minimal: HTTPX2, Pydantic V2, pydantic-settings, and typing-extensions. aiohttp remains optional and lazily imported. Test minimum supported dependencies on Python 3.10 as well as the latest compatible dependency set. Build both wheel and sdist, verify package metadata and included licenses, and name exact downstream commits when reporting compatibility. Mock tests alone do not establish TLS, pool, performance, or downstream correctness.

## Pull requests

Create a focused branch, describe the concrete problem and resulting behavior, and include relevant validation results and limitations. Update README examples, migration notes, environment examples, and the changelog when behavior changes. Preserve existing user edits. Follow the repository's review process; local validation is distinct from merging or publishing a release.

Contributions are licensed under the repository's [MIT license](LICENSE). Report security vulnerabilities privately through the project's security advisory mechanism.
