# Resource realtime progress

## Current rules

- Transport: WebSocket only.
- Wire format: JSON events only.
- gRPC: forbidden.
- protobuf: forbidden.
- Audio helpers: optional `sounddevice` + `numpy`.
- One pass = one slice = one commit.

## Slice status

| Slice | Status | Commit | Notes |
|---|---|---|---|
| 01-docs-progress-reset | done | this commit | Reset plan from protobuf to JSON. |
| 02-dependency-extras | done | this commit | Added JSON WebSocket and optional voice helper extras; removed protobuf from realtime extras. |
| 03-realtime-settings-config | done | this commit | Added realtime websocket URL setting coverage. |
| 04-client-param-types | done | this commit | Added JSON client event param types. |
| 05-server-event-models | done | this commit | Added JSON server event models and parser factory. |
| 06-client-event-serialization | done | this commit | Added JSON client event serialization and audio frame validation. |
| 07-async-websocket-connection | done | this commit | Added async JSON websocket connection and manager. |
| 08-event-handler-registry | done | this commit | Added async websocket event handlers. |
| 09-async-helper-resources | done | this commit | Added async realtime helper resources. |
| 10-async-resource-namespace | done | this commit | Added async realtime resource namespace. |
| 11-sync-websocket-connection | done | this commit | Added sync JSON websocket connection and manager. |
| 12-sync-helper-resources | done | this commit | Added sync realtime helper resources. |
| 13-sync-resource-namespace | done | this commit | Added sync realtime resource namespace. |
| 14-voice-helper-conversions | done | this commit | Added lazy numpy PCM16 conversion helpers. |
| 15-sounddevice-helpers | done | this commit | Added lazy sounddevice microphone and speaker helpers. |
| 16-examples-text-and-functions | done | this commit | Added JSON websocket text and function examples. |
| 17-example-microphone | pending |  | Add microphone realtime example. |
| 18-readme-docs | pending |  | Document resource realtime API. |
| 19-integration-smoke-tests | pending |  | Add JSON websocket integration smoke tests. |
| 20-final-audit | pending |  | Audit JSON websocket implementation. |

## Log

### 2026-04-27 — slice 01-docs-progress-reset

Done:
- Added the canonical JSON-over-WebSocket realtime implementation plan at `docs/internal/RESOURCE_REALTIME_PLAN.md`.
- Reset progress tracking from the previous protobuf plan to the JSON-only plan.
- Recorded that gRPC and protobuf are forbidden for this implementation.
- Recorded that a backend JSON WebSocket endpoint or JSON gateway must exist for integration testing.

Tests:
- not run, docs-only

Next:
- 02-dependency-extras

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke tests without a backend adapter or gateway.
- The repository still contains dependency plumbing from the previous protobuf plan; slice 02 must replace it with JSON-plan extras and remove protobuf from realtime extras.

### 2026-04-27 — slice 02-dependency-extras

Done:
- Changed `realtime` optional dependencies to WebSocket-only: `websockets>=13,<16`.
- Added `voice_helpers` optional dependencies for `sounddevice` and Python-versioned `numpy`.
- Added `realtime_voice` convenience extra with WebSocket plus voice helper dependencies.
- Removed protobuf from realtime extras to keep the SDK aligned with the JSON-only plan.

Tests:
- `uv run python -c "import gigachat"`
- `uv run pytest tests/unit/gigachat/test_client_core.py`

Next:
- 03-realtime-settings-config

Risks:
- `uv.lock` was not updated in this slice because the plan scopes slice 02 to `pyproject.toml` only.

### 2026-04-27 — slice 03-realtime-settings-config

Done:
- Verified `Settings.realtime_url` is available for the JSON WebSocket endpoint.
- Added settings tests for default `None`, constructor override, and `GIGACHAT_REALTIME_URL` env override.
- Kept the SDK from deriving a realtime endpoint from `base_url`.

Tests:
- `uv run pytest tests/unit/gigachat/test_settings.py`

Next:
- 04-client-param-types

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke tests without a backend adapter or gateway.

### 2026-04-27 — slice 04-client-param-types

Done:
- Added `gigachat.types` package exports for realtime request params.
- Added JSON realtime settings `TypedDict` params and literal aliases.
- Added JSON realtime client event params for `settings`, `input.audio_content`, `input.synthesis_content`, and `function_result`.
- Kept the slice type-only: no WebSocket transport, serialization, protobuf, or gRPC code.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_event_params.py`
- `uv run ruff check src/gigachat/types tests/unit/gigachat/realtime/test_event_params.py`
- `uv run ruff format --check src/gigachat/types tests/unit/gigachat/realtime/test_event_params.py`
- `uv run python -c "import gigachat; import gigachat.types.realtime"` (rerun outside sandbox because `uv` cache access was blocked)
- `uv run mypy src/gigachat/types tests/unit/gigachat/realtime/test_event_params.py` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 05-server-event-models

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke tests without a backend adapter or gateway.

### 2026-04-27 — slice 05-server-event-models

Done:
- Added Pydantic models for JSON realtime server events.
- Added `parse_realtime_event` with unknown-event fallback.
- Added base64 decoding for `output.audio` payloads into `bytes`.
- Added small legacy oneof-style normalization for obvious server event shapes.
- Exported realtime server event models from `gigachat.models`.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_event_models.py`
- `uv run ruff check src/gigachat/models/realtime.py src/gigachat/models/__init__.py tests/unit/gigachat/realtime/test_event_models.py`
- `uv run ruff format --check src/gigachat/models/realtime.py src/gigachat/models/__init__.py tests/unit/gigachat/realtime/test_event_models.py`
- `uv run mypy src/gigachat/models/realtime.py tests/unit/gigachat/realtime/test_event_models.py` (rerun outside sandbox because `uv` cache access was blocked)
- `uv run python -c "import gigachat; import gigachat.models.realtime"` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 06-client-event-serialization

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke tests without a backend adapter or gateway.

### 2026-04-27 — slice 06-client-event-serialization

Done:
- Added `gigachat.realtime` package exports for JSON event serialization helpers.
- Added base64 helpers for realtime audio payloads.
- Added PCM_S16LE duration calculation and validation.
- Added `serialize_client_event` for settings, input audio, synthesis, and function result client events.
- Added frame-size validation before WebSocket transport exists.
- Converted dict/list `function_result.content` values into compact JSON strings for the wire payload.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_base64_audio.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run ruff check src/gigachat/realtime tests/unit/gigachat/realtime/test_base64_audio.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run ruff format --check src/gigachat/realtime tests/unit/gigachat/realtime/test_base64_audio.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run mypy src/gigachat/realtime tests/unit/gigachat/realtime/test_base64_audio.py tests/unit/gigachat/realtime/test_event_params.py` (rerun outside sandbox because `uv` cache access was blocked)
- `uv run python -c "import gigachat; import gigachat.realtime"` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 07-async-websocket-connection

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke tests without a backend adapter or gateway.

### 2026-04-27 — slice 07-async-websocket-connection

Done:
- Added lazy `websockets` import with `gigachat[realtime]` install hint.
- Added `AsyncRealtimeConnectionManager` for resolving the realtime URL, refreshing auth, building SDK headers, opening the WebSocket, sending initial settings, and flushing queued messages.
- Added `AsyncRealtimeConnection` with `send`, `send_raw`, `recv`, `recv_bytes`, `parse_event`, `close`, and async iteration.
- Added unit coverage with a fake WebSocket connect for initial settings, auth headers, queued frames, audio JSON serialization, event parsing, close, missing URL, and missing dependency behavior.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_async_connection.py`
- `uv run pytest tests/unit/gigachat/realtime/test_async_connection.py tests/unit/gigachat/realtime/test_base64_audio.py tests/unit/gigachat/realtime/test_event_models.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run ruff check src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_async_connection.py`
- `uv run ruff format --check src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_async_connection.py`
- `uv run mypy src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_async_connection.py` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 08-event-handler-registry

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke tests without a backend adapter or gateway.

### 2026-04-27 — slice 08-event-handler-registry

Done:
- Added OpenAI-style `.on()`, `.off()`, `.once()`, and `.dispatch_events()` methods to async realtime connections.
- Added manager-level handler registration and transfer into the opened connection.
- Added specific event handlers, generic `"event"` handlers, one-shot handlers, and unhandled error event raising via `GigaChatException`.
- Kept `recv()` and async iteration parse-only: they do not raise only because an event has type `"error"`.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_async_connection.py`
- `uv run ruff check src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_async_connection.py`
- `uv run ruff format --check src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_async_connection.py`
- `uv run mypy src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_async_connection.py` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 09-async-helper-resources

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke test without a backend adapter or gateway.

### 2026-04-27 — slice 09-async-helper-resources

Done:
- Added async realtime helper resources attached to `AsyncRealtimeConnection`: `session`, `input_audio`, `synthesis`, and `function_result`.
- Added `session.send_settings(...)`, `input_audio.send(...)`, `synthesis.send(...)`, and `function_result.create(...)` helpers that delegate to `connection.send(...)`.
- Kept helpers stateless: no business state machine and no automatic function execution.
- Made `function_result.function_name` optional to match the helper contract.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_async_connection.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run ruff check src/gigachat/api/realtime.py src/gigachat/types/realtime.py tests/unit/gigachat/realtime/test_async_connection.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run ruff format --check src/gigachat/api/realtime.py src/gigachat/types/realtime.py tests/unit/gigachat/realtime/test_async_connection.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run mypy src/gigachat/api/realtime.py src/gigachat/types/realtime.py tests/unit/gigachat/realtime/test_async_connection.py tests/unit/gigachat/realtime/test_event_params.py` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 10-async-resource-namespace

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke test without a backend adapter or gateway.

### 2026-04-27 — slice 10-async-resource-namespace

Done:
- Added `AsyncRealtimeResource.connect(...)` returning `AsyncRealtimeConnectionManager`.
- Exported the async realtime resource namespace from `gigachat.resources`.
- Added cached `client.a_realtime` property on `GigaChatAsyncClient` and hybrid `GigaChat`.
- Added unit coverage for cached resource access, manager parameter forwarding, and no deprecated warnings.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_resources.py tests/unit/gigachat/test_client_lifecycle.py -q`
- `uv run ruff check src/gigachat/resources/realtime.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/realtime/test_resources.py tests/unit/gigachat/test_client_lifecycle.py`
- `uv run ruff format --check src/gigachat/resources/realtime.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/realtime/test_resources.py tests/unit/gigachat/test_client_lifecycle.py`
- `uv run mypy src/gigachat/resources/realtime.py tests/unit/gigachat/realtime/test_resources.py` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 11-sync-websocket-connection

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke test without a backend adapter or gateway.

### 2026-04-27 — slice 11-sync-websocket-connection

Done:
- Added lazy `websockets.sync.client` import with `gigachat[realtime]` install hint.
- Added `RealtimeConnectionManager` for resolving the realtime URL, refreshing sync auth, building SDK headers, opening the WebSocket, sending initial settings, and flushing queued messages.
- Added `RealtimeConnection` with `send`, `send_raw`, `recv`, `recv_bytes`, `parse_event`, `close`, sync iteration, and sync event dispatch.
- Added unit coverage with a fake sync WebSocket for initial settings, auth headers, queued frames, audio JSON serialization, event parsing, iteration, close, missing URL, missing dependency behavior, and unhandled error events.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_sync_connection.py`
- `uv run pytest tests/unit/gigachat/realtime/test_async_connection.py tests/unit/gigachat/realtime/test_sync_connection.py tests/unit/gigachat/realtime/test_base64_audio.py tests/unit/gigachat/realtime/test_event_models.py tests/unit/gigachat/realtime/test_event_params.py`
- `uv run ruff check src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_sync_connection.py`
- `uv run ruff format --check src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_sync_connection.py`
- `uv run mypy src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_sync_connection.py` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 12-sync-helper-resources

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke test without a backend adapter or gateway.

### 2026-04-27 — slice 12-sync-helper-resources

Done:
- Added sync realtime helper resources attached to `RealtimeConnection`: `session`, `input_audio`, `synthesis`, and `function_result`.
- Added `session.send_settings(...)`, `input_audio.send(...)`, `synthesis.send(...)`, and `function_result.create(...)` helpers that delegate to `connection.send(...)`.
- Kept sync helpers stateless and aligned with async helper serialization behavior.
- Made `function_result.function_name` optional to match the helper contract.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_sync_connection.py`
- `uv run ruff check src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_sync_connection.py`
- `uv run ruff format --check src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_sync_connection.py`
- `uv run mypy src/gigachat/api/realtime.py tests/unit/gigachat/realtime/test_sync_connection.py` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 14-voice-helper-conversions

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke test without a backend adapter or gateway.

### 2026-04-27 — slice 13-sync-resource-namespace

Done:
- Added `RealtimeResource.connect(...)` returning `RealtimeConnectionManager`.
- Exported the sync realtime resource namespace from `gigachat.resources`.
- Added cached `client.realtime` property on `GigaChatSyncClient` and hybrid `GigaChat`.
- Added unit coverage for cached resource access, manager parameter forwarding, and no deprecated warnings.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_resources.py tests/unit/gigachat/test_client_lifecycle.py -q`
- `uv run ruff check src/gigachat/resources/realtime.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/realtime/test_resources.py tests/unit/gigachat/test_client_lifecycle.py`
- `uv run ruff format --check src/gigachat/resources/realtime.py src/gigachat/resources/__init__.py src/gigachat/client.py tests/unit/gigachat/realtime/test_resources.py tests/unit/gigachat/test_client_lifecycle.py`
- `uv run mypy src/gigachat/resources/realtime.py tests/unit/gigachat/realtime/test_resources.py tests/unit/gigachat/test_client_lifecycle.py` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 14-voice-helper-conversions

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke test without a backend adapter or gateway.

### 2026-04-27 — slice 14-voice-helper-conversions

Done:
- Added `gigachat.realtime.audio` with lazy `numpy` loading for optional voice helper conversions.
- Added `numpy_to_pcm16_bytes(...)` for int16 PCM byte serialization, including float array clipping/scaling to PCM16.
- Added `pcm16_bytes_to_numpy(...)` for little-endian PCM16 bytes to numpy arrays.
- Exported the conversion helpers from `gigachat.realtime`.
- Added unit coverage using a fake numpy module so base installs do not require `numpy`.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_audio_helpers.py tests/unit/gigachat/realtime/test_base64_audio.py`
- `uv run ruff check src/gigachat/realtime/audio.py src/gigachat/realtime/__init__.py tests/unit/gigachat/realtime/test_audio_helpers.py`
- `uv run ruff format --check src/gigachat/realtime/audio.py src/gigachat/realtime/__init__.py tests/unit/gigachat/realtime/test_audio_helpers.py`
- `uv run mypy src/gigachat/realtime/audio.py tests/unit/gigachat/realtime/test_audio_helpers.py` (rerun outside sandbox because `uv` cache access was blocked)
- `uv run pytest tests/unit/gigachat/realtime`
- `uv run python -c "import gigachat; import gigachat.realtime"` (rerun outside sandbox because `uv` cache access was blocked)
- `uv run python -c "import gigachat; import gigachat.realtime"` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 15-sounddevice-helpers

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke test without a backend adapter or gateway.

### 2026-04-27 — slice 15-sounddevice-helpers

Done:
- Added lazy `sounddevice` loading for optional voice helper streams.
- Added `RealtimeMicrophone` as an async context manager and async iterator over PCM_S16LE bytes from `sounddevice.InputStream`.
- Added `RealtimeSpeaker` as an async context manager with queued writes to `sounddevice.OutputStream`, plus `stop()` and `close()` support.
- Exported microphone and speaker helpers from `gigachat.realtime`.
- Added unit coverage with mocked `sounddevice` streams so tests do not use real audio devices.

Tests:
- `uv run pytest tests/unit/gigachat/realtime/test_audio_helpers.py tests/unit/gigachat/realtime/test_base64_audio.py`
- `uv run ruff check src/gigachat/realtime/audio.py src/gigachat/realtime/__init__.py tests/unit/gigachat/realtime/test_audio_helpers.py`
- `uv run ruff format --check src/gigachat/realtime/audio.py src/gigachat/realtime/__init__.py tests/unit/gigachat/realtime/test_audio_helpers.py`
- `uv run mypy src/gigachat/realtime/audio.py tests/unit/gigachat/realtime/test_audio_helpers.py` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 16-examples-text-and-functions

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke test without a backend adapter or gateway.

### 2026-04-27 — slice 16-examples-text-and-functions

Done:
- Added `examples/example_realtime_text.py` with an async text-only JSON WebSocket realtime flow.
- Added `examples/example_realtime_functions.py` with a client `get_weather` function and `function_result` response.
- Documented realtime example requirements in `examples/README.md`: install `gigachat[realtime]`, set `GIGACHAT_REALTIME_URL`, and use a backend JSON WebSocket endpoint or gateway.
- Kept this slice example-only: no microphone/audio-device helper usage and no protobuf/gRPC code.

Tests:
- `uv run ruff check examples/example_realtime_text.py examples/example_realtime_functions.py`
- `uv run ruff format --check examples/example_realtime_text.py examples/example_realtime_functions.py`
- `uv run mypy examples/example_realtime_text.py examples/example_realtime_functions.py` (rerun outside sandbox because `uv` cache access was blocked)
- `uv run python -m py_compile examples/example_realtime_text.py examples/example_realtime_functions.py` (rerun outside sandbox because `uv` cache access was blocked)

Next:
- 17-example-microphone

Risks:
- Backend JSON endpoint must be confirmed. If the current GigaVoice WebSocket endpoint accepts only protobuf frames, this SDK plan cannot pass integration smoke test without a backend adapter or gateway.
