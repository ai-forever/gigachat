# Changelog

## 0.3.0a1 — unreleased alpha

- Require Python 3.10+ and use native HTTPX2 types throughout the SDK. Keep legacy HTTPX independent for other applications and dependencies.
- Add public HTTP client injection, explicit transport ownership, common TLS configuration, RequestOptions, and shared `with_options()` views.
- Consolidate request execution, token refresh, bounded retry policy, and request metadata. Preserve disabled-by-default network retries and prevent replay of partial streams.
- Add Stream/AsyncStream lifecycle management, a bounded HTTPX2 SSE decoder, fully read RawResponse wrappers, and generic binary file downloads.
- Add an opt-in aiohttp transport with owned lazy sessions, one SDK retry budget, and explicit HTTP/1.1/asyncio, timeout, and pool limitations.
- Preserve primary response extras, native Pydantic validation, existing aliases, JSON Schema keywords, and the tuple-returning structured parse interfaces.
- Replace legacy HTTPX test interception with native HTTPX2 fixtures and fail-closed cassette replay. Remove raw SSE payload logging on parse failures.

- Complete v2 streams on `response.message.done`, reject premature EOF, and preserve terminal generation errors and metadata.
- Accept base64/discard embeddings, scalar token counts, model/file metadata, open thread states, and lossless native JSON Schema.
- Add document reranking, file access updates, function validation/generation/ranking, instruction generation, batches, and thread sharing.
- Preserve empty metadata and function lists, zero message update intervals, and unknown JSON extension fields.
- Reject unexpected file-content statuses and JSON body overrides on YAML or binary endpoints.
- Remove unused private auth/retry engines and one-off release reports; consolidate migration documentation and align example linting.

See [MIGRATION.md](MIGRATION.md) for breaking changes, examples, ownership rules, downstream coordination, and limitations. This remains an alpha candidate; APIs and behavior may change before stable 0.3.0. Publication and live API validation are separate from preparation of this release.
