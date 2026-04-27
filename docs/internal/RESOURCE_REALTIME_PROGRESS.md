# Resource Realtime Progress

## Proto/doc mismatch table

| Topic | Word doc | `voice.proto` | SDK action |
|---|---|---|---|
| gRPC | WebSocket and gRPC | `service GigaVoiceService` exists | Ignore service; WebSocket only. No `pb2_grpc`. |
| `disable_interruption` | Present under `Settings` | Missing | Do not implement until field number is confirmed. |
| `enable_transcribe_silence_phrases` | Present under `Settings` | Missing | Do not serialize; document as unsupported gap. |
| `OutputTranscription.silence_phrase` | Present | Missing | Do not serialize/parse; document as unsupported gap. |
| `Platform_function_processing` | Present server event | Missing from `GigaVoiceResponse.oneof` | Do not implement; document as unsupported gap. |
| `gigachat.preset` | Present | Missing | Do not implement until proto update. |
| `Message.functions` | Present in doc | Missing | Do not implement in context model. |
| `input.synthesis_content` | Present | Proto name: `content_for_synthesis` | User-facing `send_synthesis`; wire uses `content_for_synthesis`. |
| `AudioChunkMeta.force_co_speech` | Present but description means ignore chunk | Proto name: `force_no_speech` | Canonical field `force_no_speech`, accept `force_co_speech` as alias. |
| `FunctionRanker.enable` | Present | Proto name: `enabled` | Canonical field `enable`, wire uses `enabled`. |
| `StubSounds.trigger_generation` | Present | Proto name: `trigger_delay` | Canonical field `trigger_generation`, wire uses `trigger_delay`. |
| `Settings.Mode.GIGACHAT` | Not in main doc modes | Present value 3 | Include enum as future-mode but do not feature-document heavily. |
| `GigaChatSettings.update_interval` | Not highlighted in doc | Present | Include because wire supports it. |

## Slice 01 — docs(realtime): add resource realtime codex plan

Status: done
Date: 2026-04-27

### Goal
Add the canonical Codex implementation plan and initialize progress tracking for the realtime resource work.

### Done in this slice
- Copied the realtime implementation plan into `docs/internal/RESOURCE_REALTIME_CODEX_PLAN.md`.
- Created `docs/internal/RESOURCE_REALTIME_PROGRESS.md`.
- Added the initial proto/doc mismatch table from the plan.

### Files changed
- `docs/internal/RESOURCE_REALTIME_CODEX_PLAN.md`
- `docs/internal/RESOURCE_REALTIME_PROGRESS.md`

### Tests run
- `git diff --check` — passed.

### Notes / blockers
- No blockers.

### Next slice
Slice 02 — `chore(realtime): add websocket realtime settings and extras`. Do not start it in the current run.
