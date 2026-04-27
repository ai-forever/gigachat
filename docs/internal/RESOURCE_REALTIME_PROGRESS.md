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
| 19-latest-proto-schema | pending |  | Add latest `voice.proto` exactly as provided. |
| 20-proto-message-bindings | pending |  | Add generated `voice_pb2.py`; no `voice_pb2_grpc.py`. |
| 21-protobuf-request-bridge-settings | pending |  | Map settings params to protobuf Settings. |
| 22-protobuf-client-event-serialization | pending |  | Serialize all client events to protobuf bytes. |
| 23-protobuf-server-event-parsing | pending |  | Parse protobuf responses into Pydantic events. |
| 24-async-binary-websocket-connection | pending |  | Async WS sends/receives binary protobuf frames. |
| 25-sync-binary-websocket-connection | pending |  | Sync WS sends/receives binary protobuf frames. |
| 26-helper-resources-protobuf-regression | pending |  | Ensure helpers emit protobuf requests and handlers still work. |
| 27-remove-json-wire-assumptions | pending |  | Remove stale JSON/base64 wire docs/tests/code paths. |
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
