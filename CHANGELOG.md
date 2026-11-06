# Changelog

## 0.3.0a1 — unreleased alpha

- Require Python 3.10+ and use native HTTPX2 types throughout the SDK. Keep legacy HTTPX independent for other applications and dependencies.
- Add public HTTP client injection, explicit transport ownership, common TLS configuration, RequestOptions, and shared `with_options()` views.
- Consolidate request execution, token refresh, bounded retry policy, and request metadata. Preserve disabled-by-default network retries and prevent replay of partial streams.
- Add Stream/AsyncStream lifecycle management, a bounded HTTPX2 SSE decoder, fully read RawResponse wrappers, and generic binary file downloads.
- Add an opt-in aiohttp transport with documented HTTP/1.1/asyncio, timeout, and pool limitations.
- Preserve primary response extras, native Pydantic validation, existing aliases, JSON Schema keywords, and the tuple-returning structured parse interfaces.
- Replace legacy HTTPX test interception with native HTTPX2 fixtures and fail-closed cassette replay. Remove raw SSE payload logging on parse failures.

See [MIGRATION.md](MIGRATION.md) for breaking changes, examples, ownership rules, downstream coordination, and limitations. This first alpha introduces substantial transport and lifecycle changes. Its APIs and behavior may change before the stable 0.3.0 release. This entry describes an unreleased alpha candidate; it does not claim publication or live API validation.
