# Migrating to GigaChat 0.3.0a1

This is the first alpha of the 0.3.0 series, not a stable release. It is not published yet. After publication, select it explicitly with `pip install "gigachat==0.3.0a1"`; downstream stable bounds starting at `>=0.3.0` do not select this alpha.

This release moves the SDK transport to HTTPX2 and requires Python 3.10 or newer. The primary `client.chat.create()` / `client.achat.create()` surfaces and legacy callable chat interfaces remain available. For the separate v1-to-v2 chat contract migration, see [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md).

## Python and transport types

Keep Python 3.8/3.9 applications on a compatible 0.2.x release. The dependency range is `httpx2>=2.14.0,<3`: Python 3.10 resolves to the compatible 2.14.0 line; newer interpreters can resolve newer HTTPX2 versions according to their package metadata. The universal lockfile records interpreter-specific resolutions.

Use `import httpx2` for injected clients, transports, responses, `Timeout`, and `Limits`. Legacy `httpx` may coexist for other dependencies, but its objects are not interchangeable with HTTPX2 objects. The SDK does not call `alias_httpx()` or modify another library's imports.

```python
import httpx2
from gigachat import GigaChat, RequestOptions

with httpx2.Client() as transport:
    with GigaChat(http_client=transport, model="GigaChat-2") as client:
        response = client.chat.create(
            "Hello",
            request_options=RequestOptions(timeout=httpx2.Timeout(60.0)),
        )
    assert not transport.is_closed
```

SDK-created HTTP clients are owned and closed by the SDK. Injected `http_client`, `async_http_client`, `auth_http_client`, and `auth_async_http_client` are borrowed; their caller closes them. API routing uses the SDK's configured base URL, including with an injected client. Configure TLS and transport behavior on an injected client itself.

`with_options()` returns a lightweight view sharing the owner's transport and token state. Closing a view invalidates that view without closing the owner or sibling views. A view cannot change backend, TLS, proxy, or pool settings.

For `GigaChatSyncClient`, `close()` closes the owned synchronous resources and invalidates its views. For `GigaChatAsyncClient`, use `await aclose()`. The hybrid `GigaChat.close()` closes only its synchronous side: async operations and resources remain available until `await client.aclose()`, which closes both sides. Views follow their owner's side-specific closure state. If a hybrid client uses both APIs, finish its lifetime with `await aclose()`; a synchronous context manager alone cannot close its async resources.

Async clients and their views bind to the event loop of first async use. Reusing them from another event loop raises `RuntimeError`; create a new client for that loop.

## TLS and environment

Verification remains enabled. Native HTTPX2 uses system trust by default. `ca_bundle_file` selects a CA bundle; `ssl_context` supplies a caller-owned `ssl.SSLContext`. An explicit context is not mutated. Combining it with a CA bundle, client certificate arguments, or disabled verification is rejected rather than silently choosing a winner.

```python
import ssl
from gigachat import GigaChat

context = ssl.create_default_context(cafile="/path/to/ca-bundle.pem")
context.load_cert_chain("/path/to/client.pem", "/path/to/client-key.pem")
with GigaChat(ssl_context=context) as client:
    models = client.get_models()
```

Use `auth_ssl_context` when OAuth requires a separate explicit context. `cert_file`, `key_file`, and `key_file_password` configure the API's client certificate; they are not automatically copied to OAuth. Invalid CA files and incompatible TLS arguments fail locally. `trust_env=False` disables environment proxy/CA lookup. An explicit `proxy` remains effective with `trust_env=False`.

## Request options and precedence

Every high-level request accepts `request_options=RequestOptions(...)`. Defaults compose in this order: client settings, `with_options()` view, per-call options.

```python
from gigachat import GigaChat, RequestOptions

with GigaChat(model="GigaChat-2") as client:
    view = client.with_options(timeout=60.0, max_retries=1)
    response = view.chat.create(
        "Hello",
        request_options=RequestOptions(
            timeout=90.0,
            extra_headers={"X-Request-ID": "example-request"},
            extra_query=[("tag", "one"), ("tag", "two")],
            extra_body={"future_server_option": True},
        ),
    )
```

Headers merge case-insensitively: client defaults, SDK headers, named ContextVars, `custom_headers_cvar`, view headers, then per-call headers. An explicit external `Authorization` overrides SDK authentication for that request and bypasses SDK token acquisition/refresh. Request options are not forwarded to OAuth.

Query values append in order and preserve repeated keys. JSON body precedence is `additional_fields` < typed payload < explicit `extra_body`; the final merge is shallow. `extra_body` cannot change the method's streaming mode and is rejected for multipart/binary requests. Inputs and option mappings are copied so subsequent caller mutations do not alter an in-flight request.

| Value | Meaning |
| --- | --- |
| Constructor `timeout=None`, `max_retries=None`, `max_connections=None` | Inherit settings/environment/defaults, preserving 0.2 behavior |
| Omitted `RequestOptions` field | Inherit view/client option |
| `RequestOptions(timeout=None)` | Disable network timeouts for this request |
| Constructor `timeout=httpx2.Timeout(None)` | Explicitly disable constructor network timeouts |
| `RequestOptions(max_retries=0)` | Disable network/status retries; a separate authorized 401 refresh replay remains possible |

## Retry and exceptions

`max_retries` still defaults to **0**. Opting in enables bounded retries for eligible, replayable operations only. Mutating operations and chat requests with storage state are handled conservatively. Retry-After seconds and HTTP dates are bounded by `max_retry_time`; configuring retries does not grant unlimited retry time. Auth replay is limited separately and does not reset network retry counters.

A stream is never replayed after response delivery begins. `StreamInterruptedError` exposes `request_id` and `partial_output`, and retains the original transport error as `__cause__`. Other network failures use `APIConnectionError` or `APITimeoutError`. Invalid server models use `APIResponseValidationError` with the validation failure as cause. Invalid user request models continue to raise their original validation errors.

`ResponseError` and its HTTP subclasses retain `url`, `status_code`, `content`, and `headers`, and now expose `request_id`. Existing HTTP error catches remain applicable.

## Streaming lifecycle and SSE limits

Normal iteration still works. Use `with` / `async with` or explicit `close()` / `aclose()` for deterministic early cleanup; a bare `break` does not guarantee that an arbitrary iterator is immediately closed.

```python
from gigachat import GigaChat

with GigaChat(model="GigaChat-2") as client:
    with client.chat.stream("Hello") as stream:
        for chunk in stream:
            print(chunk)
            break
```

```python
from gigachat import GigaChatAsyncClient

async def first_chunk():
    async with GigaChatAsyncClient(model="GigaChat-2") as client:
        async with client.achat.stream("Hello") as stream:
            async for chunk in stream:
                return chunk
```

Streams expose `headers`, `request_id`, `status_code`, `url`, `is_closed`, and `completed`. Lazy request metadata becomes available once the response has opened. Closing early leaves `completed=False`. Cancellation, parse failure, and exhaustion release the owned response without closing a borrowed shared client.

The common HTTPX2 EventSource decoder supports comments, multiline data, split UTF-8 bytes, LF/CR/CRLF, and `[DONE]`. A compatibility adapter flushes a final event on clean EOF without a trailing blank line; malformed/truncated JSON raises a validation error. SSE `retry` fields never cause reconnection. Named message/tool events and unknown primary-model fields remain available; no final-response accumulator is provided.

The default maximum buffered event is **1 MiB**, configurable through `max_sse_event_size` or `RequestOptions(max_sse_event_size=...)`. This is a new protective limit for formerly unbounded streams. Exceeding it raises a validation error chained from `httpx2.SSEError`. Raw chunks and prompts are not logged on parsing failures.

## Raw responses and binary downloads

```python
raw = client.chat.with_raw_response.create("Hello")
print(raw.status_code, raw.request_id, raw.headers)
completion = raw.parse()
```

The raw wrapper is fully read; `parse()` performs local conversion and is synchronous even for `raw = await client.achat.with_raw_response.create(...)`. It uses the same auth/retry/error execution path as normal chat and makes one logical request. It is distinct from `models.base.APIResponse`.

`get_file_content(file_id)` / `aget_file_content(file_id)` return binary bytes. `download_file(file_id, destination)` / `adownload_file(...)` stream in bounded chunks to a temporary file and replace the destination only after success. `get_image` continues to return its base64 specialization.

For manually consumed byte streams, use `with client.stream_file_content(file_id) as response` or `async with await client.astream_file_content(file_id) as response`. Sync `read()`/`parse()` are synchronous; async variants are awaited. Async `iter_bytes()` is consumed with `async for`. Both wrappers close their response; early iteration exit should remain inside the context manager. Byte reads and iteration translate transport failures to `APIConnectionError` or `APITimeoutError`, retaining the request ID and original cause. They never reconnect or replay already consumed bytes. A general chat `with_streaming_response` namespace is not added in this release.

## Optional aiohttp backend

Install `pip install 'gigachat[aiohttp]'` and select `async_backend="aiohttp"` explicitly, or inject `DefaultAioHttpClient`. Installing the extra does not change the default backend. Sync requests continue to use native HTTPX2.

| Capability | Native HTTPX2 | Optional aiohttp transport |
| --- | --- | --- |
| Sync / async | Both | Async only, asyncio |
| HTTP protocol | HTTP/1.1; opt-in HTTP/2 extra | HTTP/1.1 only |
| Connect / pool timeout | Independent phases | Combined connection acquisition; unequal finite values rejected |
| Write timeout | Supported | Separate finite write timeout rejected |
| Read timeout | Supported | Socket-read timeout |
| Global connection cap | Supported | Connector global connection cap |
| Separate idle connection count | Supported | Finite `max_keepalive_connections` rejected |
| Keepalive expiry | Supported | Mapped to connector policy; does not promise identical pool behavior |
| Proxy | Native HTTPX2 support | HTTP/HTTPS proxies and HTTPX2 environment routing; SOCKS rejected |
| Caller-provided session | Not applicable | Borrowed; caller closes it and owns its connector policy |

For an aiohttp timeout object, use `httpx2.Timeout(connect=30, pool=30, read=60, write=None)`. Scalar timeouts are mapped into the supported subset. For explicit limits, use `httpx2.Limits(max_connections=100, max_keepalive_connections=None)`. Unsupported options raise rather than silently losing semantics. Borrowed sessions cannot promise an SDK-selected connector cap. A borrowed session must not define default auth or an Authorization header; configure Authorization through HTTPX2 client headers or request options instead.

This transport is opt-in; no general speedup or equivalent behavior across all workloads is claimed. Local benchmark results are recorded separately in [TRANSPORT_BENCHMARK.md](artifacts/release-0.3.0/TRANSPORT_BENCHMARK.md).

## Tests, logging, and downstream consumers

Use HTTPX2 MockTransport or the repository's `tests.httpx_mock` fixtures. Legacy `pytest-httpx` monkeypatches target another package and are not the SDK's transport test mechanism. Existing cassette files are replayed through an HTTPX2 adapter with live sockets blocked; `make test-integration` is replay-only. Recording/live API requests require a separate deliberate workflow. Native transport loggers are `httpx2` / `httpcore2`; SDK loggers remain under `gigachat`.

The supplied migration baseline identified GPT2GIGA 0.3.2 at `75241ef7102617a9a1ab6300193807afa4963bc0` (`gigachat<0.3.0`) and LangChain GigaChat at `12141f854158e31486961e13db6cd355414208b0` (`gigachat==0.2.4a1`) as requiring coordinated dependency and transport-test changes. These are baseline references, not claims about their latest releases. Remove private SDK transport monkeypatches in favor of public injection and RequestOptions, and validate a candidate wheel against exact downstream commits. Installing this SDK alone does not establish downstream compatibility.

Offline tests cover request policy, SSE boundaries, cancellation, resource cleanup, raw response parsing, and binary downloads. Local socket/TLS checks and cassette replay are distinct from live GigaChat tests. No live GigaChat smoke test or public package publication is claimed by this migration guide; consult the candidate validation report for exact environments and results.


### Network settings with injected clients

Each injected API or OAuth client is authoritative for its own TLS, proxy, pool,
HTTP/2 and default timeout configuration. SDK constructor network settings apply
only to clients that the SDK creates. For example, passing `http_client=api_http`
and `proxy=proxy_url` leaves `api_http` unchanged and applies that proxy to the
SDK-created OAuth client. To use identical settings, configure and inject both
clients, or allow the SDK to create both. Per-call `RequestOptions.timeout` still
overrides the timeout of that API request without modifying either client's defaults.
