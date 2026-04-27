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
| 06-client-event-serialization | pending |  | Add JSON client event serialization. |
| 07-async-websocket-connection | pending |  | Add async JSON websocket connection. |
| 08-event-handler-registry | pending |  | Add websocket event handlers. |
| 09-async-helper-resources | pending |  | Add async realtime helper resources. |
| 10-async-resource-namespace | pending |  | Add async realtime resource namespace. |
| 11-sync-websocket-connection | pending |  | Add sync JSON websocket connection. |
| 12-sync-helper-resources | pending |  | Add sync realtime helper resources. |
| 13-sync-resource-namespace | pending |  | Add sync realtime resource namespace. |
| 14-voice-helper-conversions | pending |  | Add numpy PCM16 audio helpers. |
| 15-sounddevice-helpers | pending |  | Add sounddevice microphone and speaker helpers. |
| 16-examples-text-and-functions | pending |  | Add JSON websocket text examples. |
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
