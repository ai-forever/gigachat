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
| 02-dependency-extras | pending |  | Add optional websocket and voice helper extras. |
| 03-realtime-settings-config | pending |  | Add realtime websocket URL setting. |
| 04-client-param-types | pending |  | Add JSON client event param types. |
| 05-server-event-models | pending |  | Add JSON server event models. |
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
