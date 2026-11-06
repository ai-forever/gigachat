# Migrating to GigaChat 0.3.0a1

This guide describes the 0.3.0a1 alpha candidate. APIs may change before stable 0.3.0. Publication uses the normal release workflow; preparation of this branch does not publish a package. After publication, opt in with `pip install "gigachat==0.3.0a1"`. Bounds starting at `>=0.3.0` do not select the alpha.

This release moves the SDK transport to HTTPX2 and requires Python 3.10 or newer. The primary `client.chat.create()` / `client.achat.create()` surfaces and legacy callable chat interfaces remain available. See [Chat contract migration](#chat-contract-migration) below for the v1-to-v2 field mapping.

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

Headers merge case-insensitively: defaults on an injected HTTP client, SDK headers, named ContextVars, `custom_headers_cvar`, view headers, then per-call headers. An explicit external `Authorization` overrides SDK authentication for that request and bypasses SDK token acquisition/refresh. Request options are not forwarded to OAuth. The default session ID from settings is a fallback below explicit header sources.

Request, trace, operation, and session IDs are independent opaque values. The SDK does not create distributed traces or promise that operation IDs are span IDs. Reset ContextVars with the token from `set()` in a `finally` block; see the [README example](README.md#context-variables). New asyncio tasks inherit the creating context's snapshot; arbitrary thread executors need explicit context propagation. `authorization_cvar` supplies the complete external authorization value. `chat_url_cvar` and `chat_completions_url_cvar` override endpoint URLs, not headers.

Query values append in order and preserve repeated keys. JSON body precedence is `additional_fields` < typed payload < explicit `extra_body`; the final merge is shallow. `extra_body` cannot change the method's streaming mode and is rejected for multipart/binary/YAML requests. Inputs and option mappings are copied so subsequent caller mutations do not alter an in-flight request.

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

The common HTTPX2 EventSource decoder supports comments, multiline data, split UTF-8 bytes, and LF/CR/CRLF. The v2 stream ends after delivering `response.message.done`, preserving usage, finish reason, tool state, and error details. It closes without reading a subsequent network tail. EOF before that event raises `StreamInterruptedError`; tool events are intermediate. `completed` describes protocol completion, including a terminal payload with `finish_reason="error"`. Legacy streams retain `[DONE]` and clean-EOF compatibility. SSE `retry` fields never cause reconnection. No final-response accumulator is provided.

The default maximum buffered event is **1 MiB**, configurable through `max_sse_event_size` or `RequestOptions(max_sse_event_size=...)`. This is a new protective limit for formerly unbounded streams. Exceeding it raises a validation error chained from `httpx2.SSEError`. Raw chunks and prompts are not logged on parsing failures.

## Raw responses and binary downloads

```python
raw = client.chat.with_raw_response.create("Hello")
print(raw.status_code, raw.request_id, raw.headers)
completion = raw.parse()
```

The raw wrapper is fully read; `parse()` performs local conversion and is synchronous even for `raw = await client.achat.with_raw_response.create(...)`. It uses the same auth/retry/error execution path as normal chat and makes one logical request. It is distinct from `models.base.APIResponse`.

`get_file_content(file_id)` / `aget_file_content(file_id)` return binary bytes. `download_file(file_id, destination)` / `adownload_file(...)` stream in bounded chunks to a temporary file and replace the destination only after success. Only HTTP 200 is accepted for file content; redirects and other unexpected statuses raise `ResponseError` before replacing a destination. `get_image` continues to return its base64 specialization.

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
| Caller-provided HTTP client | Borrowed | Borrowed HTTPX2-compatible client; raw aiohttp session injection is not supported |

For an aiohttp timeout object, use `httpx2.Timeout(connect=30, pool=30, read=60, write=None)`. Scalar timeouts are mapped into the supported subset. For explicit limits, use `httpx2.Limits(max_connections=100, max_keepalive_connections=None)`. Unsupported options raise rather than silently losing semantics. All supplied timeout values must be finite and positive; `None` disables the corresponding timeout. Zero, negative, NaN, and infinite values are rejected for both client defaults and request options. Native HTTPX2 retains its own timeout semantics. The adapter creates and closes its lazy aiohttp session; the previously proposed `DefaultAioHttpClient(session=...)` argument is removed. Inject `async_http_client` or `auth_async_http_client` for a borrowed HTTPX2-compatible client. The adapter disables aiohttp connection retries so the SDK executor controls the retry budget.

This transport is opt-in; no general speedup or equivalent behavior across all workloads is claimed.

## Tests, logging, and downstream consumers

Use HTTPX2 MockTransport or the repository's `tests.httpx_mock` fixtures. Legacy `pytest-httpx` monkeypatches target another package and are not the SDK's transport test mechanism. Existing cassette files are replayed through an HTTPX2 adapter with live sockets blocked; `make test-integration` is replay-only. Recording/live API requests require a separate deliberate workflow. Native transport loggers are `httpx2` / `httpcore2`; SDK loggers remain under `gigachat`.

The supplied migration baseline identified GPT2GIGA 0.3.2 at `75241ef7102617a9a1ab6300193807afa4963bc0` (`gigachat<0.3.0`) and LangChain GigaChat at `12141f854158e31486961e13db6cd355414208b0` (`gigachat==0.2.4a1`) as requiring coordinated dependency and transport-test changes. These are baseline references, not claims about their latest releases. Remove private SDK transport monkeypatches in favor of public injection and RequestOptions, and validate a candidate wheel against exact downstream commits. Installing this SDK alone does not establish downstream compatibility.

Offline tests cover request policy, SSE boundaries, cancellation, resource cleanup, raw response parsing, and binary downloads. Local socket/TLS checks and cassette replay are distinct from live GigaChat tests. No live GigaChat smoke test or public package publication is claimed by this migration guide. Record exact environments and results in the release PR or CI.

### Network settings with injected clients

Each injected API or OAuth client is authoritative for its own TLS, proxy, pool,
HTTP/2 and default timeout configuration. SDK constructor network settings apply
only to clients that the SDK creates. For example, passing `http_client=api_http`
and `proxy=proxy_url` leaves `api_http` unchanged and applies that proxy to the
SDK-created OAuth client. To use identical settings, configure and inject both
clients, or allow the SDK to create both. Per-call `RequestOptions.timeout` still
overrides the timeout of that API request without modifying either client's defaults.


## Chat contract migration

Migration is incremental: `client.chat(payload)`, `client.stream(payload)` and
`client.chat_parse(payload, response_format=Model)` retain the v1 contract.
Their async equivalents are `achat`, `astream`, and `achat_parse`.
Use `client.chat.create`, `client.chat.stream`, and `client.chat.parse` for v2,
with `client.achat` for the corresponding async resource. Existing aliases are
not deprecated. A base URL ending in `/v1` is routed to `/v2/chat/completions`
for primary chat; an explicit `chat_completions_url` takes precedence.

| v1 | v2 |
| --- | --- |
| `Chat`, `Messages` | `ChatCompletionRequest`, `ChatMessage` |
| `ChatCompletion` | `ChatCompletionResponse` |
| `ChatCompletionChunk` import | `PrimaryChatCompletionChunk` import |
| `choices[0].message.content` | `messages[*].content[*].text` |
| `usage.prompt_tokens`, `usage.completion_tokens` | `usage.input_tokens`, `usage.output_tokens` |
| `created` | `created_at` |
| stream `choices[*].delta` | stream `messages[*].content` and `event` |

Primary content accepts a string, one part, or a list, normalized into content
parts. Responses can include multiple messages and non-text parts. Extract
assistant text explicitly rather than assuming the first part contains it:

```python
response = client.chat.create("Hello!")
for message in response.messages:
    if message.role == "assistant":
        print("".join(part.text or "" for part in message.content or []))
```

Specify a model in the request, client settings, or `GIGACHAT_MODEL`. No model
is required when an assistant or existing `storage.thread_id` selects it.
Generation parameters belong under `model_options`; top-level convenience
values are moved there, with explicit nested values taking precedence.
`response_format` and `reasoning` follow the same placement. Parse helpers
send native JSON Schema and keep the `(completion, parsed_model)` return.

For v2 function results, copy each function call's `id` into its result's `id`
and retain the originating assistant message and `tools_state_id`. Parallel
selection does not execute functions on the client. See the runnable
[roundtrip example](examples/tools/parallel_function_calling_roundtrip.py).
`ChatToolConfig.mode` accepts `auto`, `none`, `forced`, and `any`.

Primary models preserve unknown root and nested response fields. Opaque
metadata remains a dictionary or its original JSON shape. `tool_state_id` and
`functions_state_id` alias `tools_state_id`; `created` aliases `created_at`.
Use `additional_fields`, nested model extras, or `RequestOptions.extra_body`
for provider extensions. These mechanisms do not grant server permissions.
The SDK does not introduce typed wrappers for restricted endpoint families.

`storage=True` serializes as `{}`, and `storage=False` omits storage. For an
existing stored conversation use `storage.thread_id`; v1 also requires
`is_stateful=True`. `session_id` / `GIGACHAT_SESSION_ID` sets the default
`X-Session-ID` header; `session_id_cvar` can override it, then
`custom_headers_cvar`, view headers, and per-call headers. A session header does not store history or guarantee
cache hits. Thread identifiers remain accessible as `thread.id_`.

## Existing 0.2.4 schema and authentication changes

Positive token expiry values below `10_000_000_000` are normalized from seconds
to milliseconds. Zero remains the never-expiring sentinel; raw `Token.exp`
is unchanged. Native function JSON Schema retains references, composition,
boolean subschemas, extensions, and explicit null keywords. Explicit
`parameters` is preserved; flat schema shorthand keeps function metadata
separate from parameter-schema keywords.

Dictionary-valued schema `properties` remain dictionaries. Use
`parameters.properties["city"]["type"]` for a dictionary input instead of
attribute access. Explicit `FunctionParametersProperty` instances still work.
Legacy `FunctionParameters` does not add `type: object` or empty descriptions automatically.
Existing advanced helper imports remain available, but extra fields do not
implicitly become specialized helper models. Access opaque fields through
`model_extra` or their original dictionary representation.

## Open endpoint contracts in 0.3.0

Embeddings accept a string or list of strings and keyword-only
`encoding_format` and `truncate`. An embedding can be a numeric vector or a
base64 string; discard responses can contain error elements. Inspect each
item's `object_` (wire key `object`) before using its vector. `truncated` is optional. Token counting
accepts scalar input and consistently returns a list, including a one-element
list for a scalar server response.

Model metadata includes optional `type` and `features`; uploaded files include
optional `modalities`. Thread states accept `frozen` and future string values.
Thread metadata omission preserves server metadata, while `{}` clears it.
`update_interval=0` on message run/rerun requests sends tokens immediately;
this value is unrelated to network timeouts. Thread stream `usage` is optional and normally arrives in the final chunk. Assistant updates preserve
`functions=[]`. The SDK sends an explicit empty function list unchanged; the server applies
its append/overwrite rules. Omitted fields remain omitted.

Document reranking, file access updates, function validation/generation/ranking,
instruction generation, batch creation/listing, and thread sharing use the
same RequestOptions and response metadata as existing methods. Function
validation accepts the function object itself or raw YAML; HTTP 200 with
validation errors is a normal result with numeric `status`. Generated content remains text even
when the finish reason indicates an error. Function conversion sends raw
YAML with `application/x-yaml`.

Batch creation sends raw JSONL bytes or a byte stream as
`application/octet-stream`, with a `method` query parameter. Use an async byte
stream for async uploads. Batch status is an open string (including `created`,
`in_progress`, and `completed`); list/retrieve uses GET `/batches` with an optional
`batch_id` query. Both a bare JSON array (including `[]`) and a `batches` object envelope produce a `Batches` model with request metadata. Use `output_file_id` with the ordinary file download methods.
There is no scheduler, polling loop, cancellation, or pagination layer. A batch
creation is not automatically replayed after an ambiguous network failure.
Availability requires postpaid service and access to the requested models.

Thread sharing creates a read-only shared copy subject to ordinary ownership
checks. Endpoint availability still depends on the account and server; offline
contract tests cannot establish live access. The 3D object endpoint is omitted
because its binary request and multipart response contract remains incomplete.

Runnable chat, tools, schema, and metadata examples are indexed in
[examples/README.md](examples/README.md). Run examples as modules from the
repository root, with credentials and model settings in the environment.

## Internal module layout and development checks

Public imports remain available from `gigachat`, `gigachat.client`, `gigachat.assistants`, `gigachat.threads`, `gigachat.authentication`, and the existing API/model modules. The private 0.3 infrastructure now lives in six `_core` modules: `base_client`, `http_client`, `request`, `execution`, `response`, and `streaming`. Update private test imports or monkeypatch targets to their owning module; the old private root modules have no compatibility shims. Chat and file operations live in `resources`, with HTTP request builders in `api`.

Development type checks use `make ty` (`uv run ty check src tests`) instead of mypy. Python 3.10 remains the typing target, and warnings fail the check. Notebook tooling is an optional development group: install it with `uv sync --group notebook`; it is not a runtime SDK dependency.
