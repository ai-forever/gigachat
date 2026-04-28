# Resource realtime progress

## Current rules

- Transport: WebSocket only.
- Wire format: protobuf binary frames only.
- gRPC: forbidden in SDK.
- protobuf: required for realtime WebSocket frames.
- Audio helpers: optional `sounddevice` + `numpy`.
- One pass = one slice = one commit.

## Protocol pivot note

Slices 01-16 implemented an OpenAI-style realtime API shape over JSON WebSocket frames. That wire format is superseded because the actual GigaVoice backend is protobuf-over-WebSocket.

Keep and retrofit the useful API scaffolding from slices 01-16:

- `client.a_realtime` and `client.realtime` resource namespaces;
- sync/async connection lifecycle;
- event handler registry;
- helper resources: `input_audio`, `synthesis`, `function_result`, `session`;
- optional `sounddevice` + `numpy` helpers;
- `realtime_url` setting.

Replace:

- JSON frame serialization with `GigaVoiceRequest.SerializeToString()`;
- JSON frame parsing with `GigaVoiceResponse.FromString(...)`;
- base64 audio wire payloads with protobuf `bytes` fields;
- JSON endpoint/gateway docs with protobuf-over-WebSocket docs.

Do not implement gRPC. Do not generate or commit `voice_pb2_grpc.py`.

## Superseded JSON scaffold slices

| Slice | Status | Commit | Notes |
|---|---|---|---|
| 01-docs-progress-reset | done, superseded wire | this commit | JSON-only rules replaced by protobuf-over-WebSocket rules. |
| 02-dependency-extras | done, superseded wire | this commit | WebSocket/audio helper extras remain useful; protobuf must be restored in realtime extra. |
| 03-realtime-settings-config | done, keep | this commit | `realtime_url` remains canonical and must not be derived from REST `base_url`. |
| 04-client-param-types | done, retrofit | this commit | TypedDict API shape remains useful; fields must be updated to latest proto. |
| 05-server-event-models | done, retrofit | this commit | OpenAI-style event models remain useful; parser must consume protobuf responses. |
| 06-client-event-serialization | done, superseded wire | this commit | JSON serialization/base64 audio wire paths must be replaced by protobuf bytes. |
| 07-async-websocket-connection | done, retrofit | this commit | Async lifecycle remains useful; transport must send/receive binary protobuf frames. |
| 08-event-handler-registry | done, keep | this commit | Handler registry remains useful. |
| 09-async-helper-resources | done, retrofit | this commit | Helpers remain useful; emitted payloads must become protobuf requests. |
| 10-async-resource-namespace | done, keep | this commit | `client.a_realtime` namespace remains useful. |
| 11-sync-websocket-connection | done, retrofit | this commit | Sync lifecycle remains useful; transport must send/receive binary protobuf frames. |
| 12-sync-helper-resources | done, retrofit | this commit | Helpers remain useful; emitted payloads must become protobuf requests. |
| 13-sync-resource-namespace | done, keep | this commit | `client.realtime` namespace remains useful. |
| 14-voice-helper-conversions | done, keep | this commit | Optional numpy PCM helpers remain useful. |
| 15-sounddevice-helpers | done, keep | this commit | Optional microphone/speaker helpers remain useful. |
| 16-examples-text-and-functions | done, superseded docs | this commit | Examples must be updated from JSON endpoint wording to protobuf WebSocket. |

## New protobuf retrofit slice status

| Slice | Status | Commit | Notes |
|---|---|---|---|
| 17-protobuf-pivot-docs-progress | done | this commit | Pivoted docs/progress from JSON-only to protobuf-over-WebSocket. |
| 18-protobuf-runtime-extra | done | this commit | Added `protobuf` to realtime extras; no grpcio. |
| 19-latest-proto-schema | done | this commit | Added latest `voice.proto` schema and proto package markers; generated bindings are intentionally deferred. |
| 20-proto-message-bindings | done | this commit | Added generated `voice_pb2.py`; no `voice_pb2_grpc.py`. |
| 21-protobuf-request-bridge-settings | done | this commit | Map settings params to protobuf Settings. |
| 22-protobuf-client-event-serialization | done | this commit | Serialize all client events to protobuf bytes. |
| 23-protobuf-server-event-parsing | done | this commit | Parse protobuf responses into Pydantic events. |
| 24-async-binary-websocket-connection | done | this commit | Async WS sends/receives binary protobuf frames. |
| 25-sync-binary-websocket-connection | done | this commit | Sync WS sends/receives binary protobuf frames. |
| 26-helper-resources-protobuf-regression | done | this commit | Added public resource namespace regressions for helper protobuf requests and handlers. |
| 27-remove-json-wire-assumptions | done | this commit | Removed stale JSON/base64 wire docs/tests/code paths. |
| 28-examples-protobuf-websocket | pending |  | Update examples to protobuf-over-WebSocket. |
| 29-integration-smoke-protobuf-ws | pending |  | Optional backend smoke tests. |
| 30-docs-readme-protobuf-realtime | pending |  | README/API docs for protobuf realtime. |
| 31-final-protobuf-audit | pending |  | Final no-gRPC/no-JSON-wire audit. |

## Log

### 2026-04-28 — slice 17-protobuf-pivot-docs-progress

Done:
- Pivoted the canonical resource realtime plan from JSON WebSocket frames to protobuf binary WebSocket frames.
- Kept WebSocket-only and no-gRPC constraints.
- Recorded that protobuf is required for the actual backend.
- Marked JSON slices 01-16 as reusable API scaffolding but superseded wire implementation.
- Added protobuf retrofit slices 18-31.

Tests:
- not run, docs-only

Next:
- 18-protobuf-runtime-extra

Risks:
- Assumes one WebSocket binary frame equals one serialized `GigaVoiceRequest` / `GigaVoiceResponse` without length-prefix.
- Requires generated `voice_pb2.py` to be committed because users should not run proto generation at install time.

### 2026-04-28 — slice 18-protobuf-runtime-extra

Done:
- Added `protobuf>=4.25,<6` to the `realtime` optional dependency extra.
- Added `protobuf>=4.25,<6` to `realtime_voice` so the combined realtime voice extra includes both protobuf WebSocket transport and audio helpers.
- Kept protobuf out of core runtime dependencies.
- Confirmed no `grpcio` dependency was added.

Tests:
- `uv lock --check`
- `rg -n "grpcio|^name = \"grpc" pyproject.toml uv.lock` (no matches)

Next:
- 19-latest-proto-schema

Risks:
- Next slice must add the exact latest `voice.proto`; this slice only adds the protobuf runtime dependency.

### 2026-04-28 — slice 19-latest-proto-schema

Done:
- Added the latest `src/gigachat/proto/gigavoice/voice.proto` schema as the source for realtime protobuf messages.
- Added package marker files for `gigachat.proto` and `gigachat.proto.gigavoice`.
- Kept this slice schema-only: no generated `voice_pb2.py`, no `voice_pb2_grpc.py`, and no gRPC runtime dependency.

Tests:
- `uv run python -c "import gigachat"`

Next:
- 20-proto-message-bindings

Risks:
- The proto text includes `service GigaVoiceService`; the next slice must generate only Python message bindings and must not commit gRPC stubs.

### 2026-04-28 — slice 20-proto-message-bindings

Done:
- Generated `src/gigachat/proto/gigavoice/voice_pb2.py` from `voice.proto`.
- Used a one-off `grpc_tools.protoc` invocation pinned to protobuf 5.x-compatible gencode because system `protoc` 34.0 generated bindings requiring protobuf 7.34.0.
- Did not generate or add `voice_pb2_grpc.py`.
- Added import and round-trip coverage for `GigaVoiceRequest`, `GigaVoiceResponse`, and raw audio bytes.
- Excluded generated `*_pb2.py` files from Ruff and mypy source scanning, and marked the generated file itself to skip direct Ruff/mypy checks; tests access generated message classes dynamically because mypy cannot infer protobuf builder-created attributes.

Tests:
- `uv run python -c "from gigachat.proto.gigavoice import voice_pb2; req = voice_pb2.GigaVoiceRequest(settings=voice_pb2.Settings(voice_call_id='x')); data = req.SerializeToString(); parsed = voice_pb2.GigaVoiceRequest.FromString(data); print(type(data).__name__, len(data), parsed.WhichOneof('request'), parsed.settings.voice_call_id)"`
- `uv run pytest tests/unit/gigachat/realtime/test_proto_imports.py`
- `uv run ruff check src/gigachat/proto/gigavoice/voice_pb2.py tests/unit/gigachat/realtime/test_proto_imports.py`
- `uv run mypy src/gigachat/proto/gigavoice/voice_pb2.py tests/unit/gigachat/realtime/test_proto_imports.py`
- `uv run ruff check src tests`
- `uv run mypy src tests`
- `find src/gigachat/proto/gigavoice -name '*grpc*' -print` (no output)
- `rg -n "grpcio|^name = \"grpc" pyproject.toml uv.lock` (no matches)

Next:
- 21-protobuf-request-bridge-settings

Risks:
- The generated descriptor still contains the `GigaVoiceService` service descriptor from `voice.proto`; this is expected for message bindings and must not be confused with a gRPC transport implementation.

### 2026-04-28 — slice 21-protobuf-request-bridge-settings

Done:
- Added latest proto enum literals and settings TypedDict fields for mode/output/audio/content/stub sounds/function ranker/filter settings/function schemas.
- Added `src/gigachat/realtime/_protobuf.py` with `settings_to_pb(...)`, duration conversion, enum lookup, compact JSON-string conversion, and nested settings mapping.
- Mapped `function_ranker.enable` as a compatibility alias for `enabled`, with conflict validation.
- Added protobuf settings serialization coverage for minimal and full settings, durations, enum errors, JSON-string helpers, and missing `voice_call_id`.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_protobuf_client_serialization.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run ruff check src/gigachat/realtime/_protobuf.py src/gigachat/types/realtime.py tests/unit/gigachat/realtime/test_protobuf_client_serialization.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run mypy src/gigachat/realtime/_protobuf.py src/gigachat/types/realtime.py tests/unit/gigachat/realtime/test_protobuf_client_serialization.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run pytest tests/unit/gigachat/realtime`
- `uv run ruff check src tests`
- `uv run mypy src tests`
- `uv run pytest`

Next:
- 22-protobuf-client-event-serialization

Risks:
- WebSocket transport still sends JSON frames until slice 24/25; this slice only builds protobuf `Settings`.

### 2026-04-28 — slice 22-protobuf-client-event-serialization

Done:
- Added `client_event_to_request(...)` for settings, audio content, synthesis content, and function result client events.
- Added protobuf `serialize_client_event(...) -> bytes` with binary frame size validation.
- Preserved raw audio bytes in `AudioContent.audio_chunk`; no base64 is used by the protobuf serializer.
- Added audio meta mapping for canonical `force_no_speech` and compatibility alias `force_co_speech`, including conflict validation.
- Added lower/upper content type alias mapping for synthesis and compact JSON-string conversion for mapping/list function results.
- Exported the protobuf serializer helpers from `gigachat.realtime`.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_protobuf_client_serialization.py`
- `uv run ruff check src/gigachat/realtime/_protobuf.py src/gigachat/realtime/__init__.py tests/unit/gigachat/realtime/test_protobuf_client_serialization.py`
- `uv run mypy src/gigachat/realtime/_protobuf.py src/gigachat/realtime/__init__.py tests/unit/gigachat/realtime/test_protobuf_client_serialization.py`

Next:
- 23-protobuf-server-event-parsing

Risks:
- WebSocket transport still imports the JSON `_events.serialize_client_event` path until slices 24/25 switch async/sync connections to binary protobuf frames.

### 2026-04-28 — slice 23-protobuf-server-event-parsing

Done:
- Added `parse_server_event(...)` for binary `GigaVoiceResponse` protobuf frames.
- Added `response_to_event(...)` and response oneof mapping for output audio/additional data/interrupted, function calls, input/output transcriptions, errors, warnings, input files, and platform function processing.
- Converted protobuf `Duration` to seconds floats for output audio duration.
- Exposed protobuf enum names for `input_transcription.person_identity.age` and `gender`.
- Added server parsing regression tests for every `GigaVoiceResponse` oneof, including `output_transcription.silence_phrase`, `input_transcription.person_identity`, `input_transcription.emotion`, `input_files`, and invalid/empty frames.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_protobuf_server_parsing.py`
- `uv run ruff check src/gigachat/realtime/_protobuf.py src/gigachat/realtime/__init__.py tests/unit/gigachat/realtime/test_protobuf_server_parsing.py`
- `uv run mypy src/gigachat/realtime/_protobuf.py src/gigachat/realtime/__init__.py tests/unit/gigachat/realtime/test_protobuf_server_parsing.py`
- `uv run pytest tests/unit/gigachat/realtime`
- `uv run ruff check src tests`
- `uv run mypy src tests`

Next:
- 24-async-binary-websocket-connection

Risks:
- WebSocket transport still parses JSON frames until slice 24 switches the async connection to binary protobuf `parse_server_event(...)`.

### 2026-04-28 — slice 24-async-binary-websocket-connection

Done:
- Switched async realtime connection send path to serialize client events as protobuf `GigaVoiceRequest` bytes.
- Switched initial async settings frame and async helper resources to send binary protobuf frames.
- Switched async `recv()` / `parse_event()` to parse binary `GigaVoiceResponse` frames.
- Made async `send_raw()` accept bytes only and made async `recv_bytes()` reject text frames with a protocol error.
- Kept protobuf bridge imports lazy inside `gigachat.api.realtime` so `import gigachat` does not eagerly import protobuf realtime bridge code.
- Updated async connection tests to assert sent protobuf requests and feed protobuf server responses.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_async_connection.py`
- `uv run pytest tests/unit/gigachat/realtime`
- `uv run python -c "import gigachat"`
- `uv run ruff check src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_async_connection.py`
- `uv run ruff check src tests`
- `uv run mypy src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_async_connection.py`
- `uv run mypy src tests`

Next:
- 25-sync-binary-websocket-connection

Risks:
- Sync realtime connection still sends/parses JSON frames until slice 25.

### 2026-04-28 — slice 25-sync-binary-websocket-connection

Done:
- Switched sync realtime connection send path to serialize client events as protobuf `GigaVoiceRequest` bytes.
- Switched initial sync settings frame and sync helper resources to send binary protobuf frames.
- Switched sync `recv()` / `parse_event()` to parse binary `GigaVoiceResponse` frames.
- Made sync `send_raw()` accept bytes only and made sync `recv_bytes()` reject text frames with a protocol error.
- Updated sync connection tests to assert sent protobuf requests and feed protobuf server responses.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_sync_connection.py`
- `uv run ruff check src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_sync_connection.py`
- `uv run mypy src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_sync_connection.py`
- `uv run pytest tests/unit/gigachat/realtime`
- `uv run ruff check src tests`
- `uv run mypy src tests`
- `uv run pytest`

Next:
- 26-helper-resources-protobuf-regression

Risks:
- Helper resources now send protobuf through both async and sync connection paths; the next slice should add focused regression coverage at the resource namespace level.

### 2026-04-28 — slice 26-helper-resources-protobuf-regression

Done:
- Added public `client.a_realtime.connect(...)` and `client.realtime.connect(...)` regression coverage using fake WebSocket connectors.
- Verified `session` initial settings, `input_audio`, `synthesis`, and `function_result` helpers emit binary protobuf `GigaVoiceRequest` frames through the resource namespace.
- Verified resource-level event handlers registered on the manager are copied into the active connection and dispatched from protobuf server frames.
- Added the canonical `force_no_speech` audio meta key to `RealtimeAudioChunkMetaParam` while keeping the compatibility alias `force_co_speech`.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_resources.py`
- `uv run ruff check src/gigachat/types/realtime.py tests/unit/gigachat/realtime/test_resources.py`
- `uv run mypy src/gigachat/types/realtime.py tests/unit/gigachat/realtime/test_resources.py`
- `uv run pytest tests/unit/gigachat/realtime`
- `uv run ruff check src tests`
- `uv run mypy src tests`

Next:
- 27-remove-json-wire-assumptions

Risks:
- This slice covers resource namespace regressions with fake WebSocket connectors only; backend smoke coverage remains deferred to slice 29.

### 2026-04-28 — slice 27-remove-json-wire-assumptions

Done:
- Removed the private JSON WebSocket serializer module `gigachat.realtime._events`.
- Moved realtime frame/audio validation constants to `gigachat.realtime._constants` so resource defaults do not depend on JSON serialization code.
- Removed base64 string decoding from `OutputAudioEvent`; protobuf response audio now stays raw `bytes`.
- Removed legacy JSON-oneof event normalization from `parse_realtime_event(...)`.
- Removed JSON/base64 wire serialization assertions from realtime event-param tests; protobuf serializer coverage remains in `test_protobuf_client_serialization.py`.
- Updated realtime example wording and examples README from JSON endpoint/gateway language to protobuf binary WebSocket language.
- Stopped exporting `encode_audio` / `decode_audio` from `gigachat.realtime`; the private `_base64.py` helpers remain only for legacy helper coverage and PCM duration validation.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_event_params.py tests/unit/gigachat/realtime/test_event_models.py tests/unit/gigachat/realtime/test_protobuf_client_serialization.py tests/unit/gigachat/realtime/test_protobuf_server_parsing.py tests/unit/gigachat/realtime/test_async_connection.py tests/unit/gigachat/realtime/test_sync_connection.py tests/unit/gigachat/realtime/test_resources.py`
- `uv run pytest tests/unit/gigachat/realtime`
- `uv run ruff check src/gigachat/realtime/_constants.py src/gigachat/realtime/_protobuf.py src/gigachat/api/realtime.py src/gigachat/resources/realtime.py src/gigachat/realtime/__init__.py src/gigachat/models/realtime.py tests/unit/gigachat/realtime/test_event_params.py tests/unit/gigachat/realtime/test_event_models.py examples/example_realtime_text.py examples/example_realtime_functions.py`
- `uv run mypy src/gigachat/realtime/_constants.py src/gigachat/realtime/_protobuf.py src/gigachat/api/realtime.py src/gigachat/resources/realtime.py src/gigachat/realtime/__init__.py src/gigachat/models/realtime.py tests/unit/gigachat/realtime/test_event_params.py tests/unit/gigachat/realtime/test_event_models.py`
- `rg -n "realtime\._events|_events\.py|JSON events over WebSocket|JSON WebSocket|JSON endpoint|json-realtime|base64.*wire|wire.*base64|protobuf: forbidden|voice_pb2_grpc|grpcio|transport=\"grpc\"" src/gigachat tests/unit/gigachat/realtime examples` (no matches)
- `uv run ruff check src tests examples/example_realtime_text.py examples/example_realtime_functions.py`
- `uv run mypy src tests`
- `uv run pytest`

Next:
- 28-examples-protobuf-websocket

Risks:
- `_base64.py` still exists as a private legacy helper module for encode/decode tests and shared PCM duration validation; it is not used by realtime transport or exported from `gigachat.realtime`.
