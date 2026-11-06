# GigaChat 0.3.0 series validation

**Alpha designation:** The current candidate is `0.3.0a1` (Development Status: Alpha). The full matrix below was completed before this version-only metadata change, with the same runtime source. See [ALPHA_BUILD.md](ALPHA_BUILD.md) for the current artifacts and packaging verification. Previous `0.3.0` artifacts were unpublished build candidates, not releases.

Date: 2026-11-06. Environment: macOS ARM64. Source: the local, uncommitted implementation working tree.

**Final result: 950 tests passed plus 33 strict cassette replay tests passed in every environment below.** This includes Python 3.10 with both the lowest declared direct dependencies and the latest compatible lock, and Python 3.11 through 3.15 with the latest compatible lock.

## Baseline

Before dependency and fixture migration, Python 3.12 ran **636 unit tests successfully**, with 33 integration tests deselected. The 33 existing cassette tests also passed when collected separately, with dummy OAuth settings and legacy HTTPX environment-proxy inheritance disabled. Full original test collection could import examples that load `.env` and contaminate integration credentials; the new replay fixture is independent of those settings.

## Python and dependency matrix

All environments use Pydantic 2.14.3, aiohttp 3.14.5 and typing-extensions 4.16.0. The minimum environment resolves the lowest declared direct dependencies. Latest environments use the single universal `uv.lock`. The unit column excludes the 33 integration tests; the cassette column runs them separately.

| Environment | Python | HTTPX2 / httpcore2 | pydantic-settings | Unit/contract/wire tests | Strict cassette replay |
|---|---|---|---|---|---|
| minimum-3.10 | 3.10.19 | 2.14.0 / 2.14.0 | 2.15.0 | 950 passed (4.84 s) | 33 passed (0.40 s) |
| latest-3.10 | 3.10.19 | 2.14.0 / 2.14.0 | 2.15.0 | 950 passed (2.96 s) | 33 passed (0.37 s) |
| latest-3.11 | 3.11.14 | 2.16.0 / 2.16.0 | 2.16.2 | 950 passed (2.54 s) | 33 passed (0.31 s) |
| latest-3.12 | 3.12.12 | 2.16.0 / 2.16.0 | 2.16.2 | 950 passed (2.61 s) | 33 passed (0.27 s) |
| latest-3.13 | 3.13.8 | 2.16.0 / 2.16.0 | 2.16.2 | 950 passed (2.63 s) | 33 passed (0.27 s) |
| latest-3.14 | 3.14.3 | 2.16.0 / 2.16.0 | 2.16.2 | 950 passed (2.45 s) | 33 passed (0.21 s) |
| latest-3.15 | 3.15.0 | 2.16.0 / 2.16.0 | 2.16.2 | 950 passed (2.73 s) | 33 passed (0.29 s) |

Exact package and tool versions are recorded in [versions.json](versions.json); complete successful test output is retained in [logs/](logs/). The minimum environment uses pytest 9.0.0, pytest-asyncio 1.3.0, Ruff 0.14.9 and mypy 1.19.0. Latest environments use pytest 9.2.0, pytest-asyncio 1.4.1.post1, Ruff 0.17.4 and mypy 1.20.2.

## Commands

Latest environments were installed without changing the shared lock:

```sh
UV_PROJECT_ENVIRONMENT=/private/tmp/gigachat-latest310 UV_CACHE_DIR=/private/tmp/gigachat-uv-cache \
  uv sync --frozen --python 3.10 --all-extras --dev
# Repeat for Python 3.11 through 3.15 with separate environment paths.
```

The minimum environment was installed separately from the project metadata:

```sh
UV_CACHE_DIR=/private/tmp/gigachat-uv-cache uv venv /private/tmp/gigachat-min310 --python 3.10
UV_CACHE_DIR=/private/tmp/gigachat-uv-cache uv pip install \
  --python /private/tmp/gigachat-min310/bin/python --requirements pyproject.toml \
  --all-extras --group dev --resolution lowest-direct
```

Each environment ran these commands from the repository root:

```sh
<environment>/bin/python -m pytest -q --tb=short
<environment>/bin/python -m pytest -q -m integration --record-mode=none tests/integration
```

Local HTTP/TLS tests require loopback socket binding. They ran with that permission enabled after the filesystem sandbox rejected binds to `127.0.0.1`. These are local fixtures, including custom CA, mTLS, proxy, connection-pool limits, cancellation, chunked uploads and interrupted streams.

## Test infrastructure and contracts

The replacement fixture uses native `httpx2.MockTransport` and native request/response classes. Mocked responses are consumed explicitly once; unexpected requests fail. Cassette replay matches method, scheme, host, port, path, query pairs (including duplicates), and request body. JSON formatting/key order are normalized while boolean and numeric values remain distinct. Only recorded OAuth scope redaction is reproduced. Socket connect/connect_ex are blocked during all cassette replay.

Old recordings contain redundant OAuth refreshes caused by the previous token-expiry interpretation. Unused copies of an already-consumed matching OAuth interaction may remain; unused API responses fail. No unmatched request can fall back to live network access.

Dictionary-level header tests retain the historical canonical keys used by downstream callers, including `Authorization`, `User-Agent` and `X-Session-ID`. Lowercase custom overrides are merged case-insensitively without changing those keys; unknown header spelling is preserved. Separate assertions also verify native case-insensitive wire-header behavior. Unexpected streaming Content-Type is a nonretryable SDK validation error with request metadata.

The focused executor suite passes 209 cases covering endpoint option propagation and exactly one 401 replay across 36 sync and async entry points; status retry budgets; late-401 token generations; concurrent refresh and cancellation recovery; OAuth isolation; request snapshots and precedence; payload immutability; seekable/nonseekable upload replay; stream retry boundaries; borrowed ownership; view invalidation; hybrid lifecycle; cross-event-loop rejection; absolute password-token routing; lazy stream input snapshots; preserved input-validation errors; default header/cookie/query/timeout snapshots; nested same-view/different-view callback isolation; and shared owner-token access through views.

## Packaging

`uv build` built the source distribution and then a wheel from that source distribution. Wheel metadata declares version 0.3.0, Python >=3.10,<4, HTTPX2 >=2.14,<3 and the three optional extras. The wheel includes `py.typed` and license files. The source distribution includes its README, license and build metadata.

A clean base-wheel install on Python 3.10 resolved HTTPX2 2.14.0/settings 2.15.0. A clean base-wheel install on Python 3.15 resolved HTTPX2 2.16.0/settings 2.16.2. Both imported the SDK and constructed native sync/async clients with neither legacy `httpx` nor `aiohttp` installed. Constructing `DefaultAioHttpClient` without its extra raised an actionable ImportError.

A clean Python 3.10 wheel install with `[aiohttp,http2,socks]` resolved and imported all extras. HTTP/2, SOCKS-proxy and aiohttp client construction passed without making network requests. Borrowed aiohttp sessions with default authentication or an Authorization header were rejected before transport I/O; revalidation also rejected credentials added after client construction while preserving caller session ownership.

The repository wheel and source distribution were rebuilt after the final compatibility audit. Every packaged source/provenance file, including the vendor license and `FORK.md`, was compared byte-for-byte against the current `src/gigachat` tree. The final wheel was reinstalled into all clean smoke environments. Results and candidate SHA-256 values are recorded in [package-smoke.json](package-smoke.json).

A separate wheel install alongside actual legacy HTTPX 0.28.1 confirmed distinct module/object families: legacy Client, Timeout and Limits objects and per-request legacy Timeout were rejected; native HTTPX2 client injection completed a mocked request.

```sh
UV_CACHE_DIR=/private/tmp/gigachat-uv-cache uv build --out-dir dist
uv pip install --python <clean-environment>/bin/python \
  dist/gigachat-0.3.0-py3-none-any.whl
# For optional transports:
uv pip install --python <clean-environment>/bin/python \
  'dist/gigachat-0.3.0-py3-none-any.whl[aiohttp,http2,socks]'
```

### Final distribution SHA-256

- `dist/gigachat-0.3.0-py3-none-any.whl`: `3b8cc523f0715f9a0350e407d430cd6bb6a303aa33d80baca4522300c80d2d5a`
- `dist/gigachat-0.3.0.tar.gz`: `aa3a86398258c4b6270db39cfb6070dd19cf6fe14295982e05d383166623c754`

## Static checks

- `mypy src tests`: passed, 113 source files.
- `ruff check src tests`: passed.
- `ruff format --check src tests`: passed, 110 files.
- `uv lock --check`: passed, 68 resolved packages.

## Scope of evidence

No live GigaChat request, release publication, git commit, push or merge was performed. Passing offline, cassette and local-wire tests does not measure live service reliability, throughput, quality, downstream compatibility or production TLS/proxy configuration. The configured Ubuntu CI jobs were not executed by this local validation. Separate downstream work is recorded in [downstream/REPORT.md](downstream/REPORT.md).
