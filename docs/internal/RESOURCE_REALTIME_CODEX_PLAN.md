# План реализации `resource realtime` для GigaVoice WebSocket в `gigachat`

Документ предназначен для GPT-5.5 Codex, который будет работать в ветке `feature/resource-api-non-chat` из PR #110.

Главная цель: добавить в SDK новый Resource API namespace для voice realtime:

```python
client.realtime      # sync WebSocket API
client.a_realtime    # async WebSocket API
```

Важно: **gRPC в SDK не делаем**. Реализация только WebSocket + protobuf.

---

## 0. Жёсткие правила для Codex

1. **Нельзя брать больше одной задачи за один заход.**
   - Выбери первый незавершённый slice из раздела `10. Commit-срезы`.
   - Сделай только его.
   - Сделай один commit.
   - Остановись и отчитайся.

2. **Каждый slice обязан обновлять progress-файл.**
   - Progress-файл в репозитории: `docs/internal/RESOURCE_REALTIME_PROGRESS.md`.
   - В каждом commit должен быть diff этого файла.
   - Формат записи см. раздел `9. Progress protocol`.

3. **Не добавлять gRPC.**
   - Не добавлять `grpcio`, `grpcio-tools` в runtime dependencies.
   - Не генерировать и не коммитить `voice_pb2_grpc.py`.
   - Не добавлять `transport="grpc"`.
   - Не добавлять `GigaVoiceService`-клиент.
   - В proto может остаться `service GigaVoiceService`, потому что он есть в исходном `voice.proto`, но SDK его не использует.

4. **Не угадывать поля, которых нет в `voice.proto`.**
   - Если поле есть в Word-документе, но отсутствует в proto, нельзя придумывать field number.
   - Такие поля фиксировать в gap-table и не сериализовать.

5. **Не угадывать WebSocket endpoint.**
   - В SDK добавить настройку `realtime_url`.
   - Если `url` не передан в `connect()` и `GIGACHAT_REALTIME_URL` не задан, выбрасывать понятный `ValueError`.

6. **Не ломать импорт `gigachat` без realtime extra.**
   - `protobuf` и `websockets` должны быть optional.
   - Любые импорты `voice_pb2` и `websockets` делать lazy там, где реально нужен realtime.
   - `import gigachat` должен работать без `pip install "gigachat[realtime]"`.

7. **Не добавлять root-level deprecated shim.**
   - Старого `client.voice(...)` или `client.realtime(...)` как метода не было.
   - Canonical path сразу resource-style: `client.realtime.connect(...)`, `client.a_realtime.connect(...)`.

8. **Писать код под Python 3.8+.**
   - Не использовать `X | Y` type union.
   - Использовать `Optional`, `Union`, `List`, `Dict`, `Tuple`.
   - Учитывать `mypy strict`.

---

## 1. Что такое `resource realtime`

`resource realtime` — это **новый Resource API namespace в Python SDK**, а не новый backend enum.

Правильно:

```python
async with client.a_realtime.connect(settings, url="wss://...") as session:
    await session.send_audio(chunk, speech_start=True)
```

Неправильно:

```python
# Не добавлять такой enum, его нет в proto.
RealtimeMode.RESOURCE_REALTIME
```

Backend modes из proto остаются такими:

```text
MODE_UNSPECIFIED = 0
RECOGNIZE_GIGACHAT_SYNTHESIS = 1
GIGACHAT_SYNTHESIS = 2
GIGACHAT = 3                 # есть в proto, future-mode
RECOGNIZE_SYNTHESIS = 4
```

---

## 2. Источники правды

Использовать два источника:

1. `voice.proto` — **источник правды для wire-schema**.
   - Всё, что сериализуется в protobuf, должно иметь поле в proto.
   - Если в Word-документе поле есть, но в proto его нет, оно не wire-capable.

2. `gigavoice.docx` — **источник бизнес-семантики**.
   - Последовательность событий.
   - Ограничения.
   - Что означает `interrupted`, `is_final`, `voice_call_id`, modes, VAD и т.д.

Ключевые требования из документа:

- Протокол: WebSocket, внутри protobuf.
- Первый client message после открытия соединения — `settings`.
- Далее клиент отправляет `input.audio_content`, `input.synthesis_content` или `function_result`.
- Сервер возвращает один из событий: `output`, `function_call`, `input_transcription`, `output_transcription`, `error`, `warning`, `input_files`.
- `output.audio.is_final = true` или `output.interrupted = true` означает завершение текущей аудио-генерации.
- Для `output_modalities = TEXT` завершение ответа определяется получением `output_transcription` и `output.additional_data`.
- `voice_call_id` обязателен, должен быть UUID и сохраняться при reconnect той же сессии.
- Размер одного protobuf message — не более 4 МБ.
- Один аудио-чанк — не более 2 секунд.
- SDK не должен автоматически восстанавливать сессию после reconnect: пользователь сам собирает контекст и передаёт его в `settings.context` нового соединения.

---

## 3. Public API, который должен получиться

### 3.1 Async API

`client.a_realtime.connect(...)` должен возвращать async context manager.

```python
from uuid import uuid4

from gigachat import GigaChat
from gigachat.models.realtime import (
    RealtimeAudioEncoding,
    RealtimeAudioSettings,
    RealtimeInputAudioSettings,
    RealtimeMode,
    RealtimeOutputModalities,
    RealtimeSettings,
)

settings = RealtimeSettings(
    voice_call_id=str(uuid4()),
    mode=RealtimeMode.RECOGNIZE_GIGACHAT_SYNTHESIS,
    output_modalities=RealtimeOutputModalities.AUDIO_TEXT,
    enable_transcribe_input=True,
    audio=RealtimeAudioSettings(
        input=RealtimeInputAudioSettings(
            audio_encoding=RealtimeAudioEncoding.PCM_S16LE,
            sample_rate=16000,
        ),
    ),
)

async with GigaChat(credentials="...") as client:
    async with client.a_realtime.connect(settings, url="wss://...") as session:
        await session.send_audio(audio_chunk, speech_start=True)

        async for event in session:
            if event.input_transcription:
                print(event.input_transcription.text)

            if event.output and event.output.audio:
                play(event.output.audio.audio_chunk)

            if event.output and event.output.interrupted:
                stop_playback()
```

Design detail: `connect()` должен быть обычным методом, который возвращает объект с `__aenter__`, а не coroutine. Это позволяет писать:

```python
async with client.a_realtime.connect(settings) as session:
    ...
```

а не:

```python
async with await client.a_realtime.connect(settings) as session:
    ...
```

### 3.2 Sync API

`client.realtime.connect(...)` должен возвращать sync context manager.

```python
with GigaChat(credentials="...") as client:
    with client.realtime.connect(settings, url="wss://...") as session:
        session.send_audio(audio_chunk, speech_start=True)
        for event in session:
            ...
```

Sync API делается отдельным slice после async API.

### 3.3 Session helpers

Минимальный набор методов session:

```python
# async
await session.send_audio(
    audio_chunk: bytes,
    speech_start: Optional[bool] = None,
    speech_end: Optional[bool] = None,
    force_no_speech: Optional[bool] = None,
)

await session.send_synthesis(
    text: str,
    content_type: RealtimeSynthesisContentType = RealtimeSynthesisContentType.TEXT,
    is_final: bool = False,
)

await session.send_function_result(
    content: Union[str, Dict[str, Any]],
    function_name: Optional[str] = None,
)

event = await session.receive()
async for event in session:
    ...
```

Sync методы имеют те же имена, но без `await`.

---

## 4. Файловая архитектура

Добавить:

```text
src/gigachat/proto/__init__.py
src/gigachat/proto/gigavoice/__init__.py
src/gigachat/proto/gigavoice/voice.proto
src/gigachat/proto/gigavoice/voice_pb2.py

src/gigachat/models/realtime.py
src/gigachat/api/realtime.py
src/gigachat/resources/realtime.py

docs/internal/RESOURCE_REALTIME_CODEX_PLAN.md
docs/internal/RESOURCE_REALTIME_PROGRESS.md

examples/example_realtime_voice.py
examples/example_realtime_synthesis_only.py
examples/example_realtime_text_output.py

tests/unit/gigachat/models/test_realtime_settings.py
tests/unit/gigachat/models/test_realtime_requests.py
tests/unit/gigachat/models/test_realtime_responses.py
tests/unit/gigachat/api/test_realtime_websocket.py
tests/unit/gigachat/test_client_realtime_resources.py
```

Изменить:

```text
pyproject.toml
src/gigachat/client.py
src/gigachat/settings.py
src/gigachat/resources/__init__.py
src/gigachat/models/__init__.py
README.md
MIGRATION_GUIDE.md
MIGRATION_GUIDE_ru.md
```

Не добавлять:

```text
src/gigachat/proto/gigavoice/voice_pb2_grpc.py
src/gigachat/api/realtime_grpc.py
```

---

## 5. Dependencies и import policy

В `pyproject.toml` добавить optional extra:

```toml
[project.optional-dependencies]
realtime = [
    "protobuf>=4,<6",
    "websockets>=12,<16",
]
```

Правила:

- `protobuf` и `websockets` не должны стать hard dependency, если maintainers явно не попросят.
- Импорт `gigachat`, `gigachat.client`, `gigachat.resources` должен проходить без realtime extra.
- `gigachat.models.realtime` может импортироваться без protobuf, если методы `to_pb()` / `from_pb()` делают lazy import.
- Если пользователь вызывает realtime без extra, поднять:

```python
ImportError(
    "Realtime WebSocket support requires optional dependencies. "
    "Install them with `pip install 'gigachat[realtime]'`."
)
```

---

## 6. Settings и URL

В `Settings` добавить:

```python
realtime_url: Optional[str] = Field(
    default=None,
    description="WebSocket URL for GigaVoice realtime API.",
)
```

В `_BaseClient.__init__`, `GigaChatSyncClient.__init__`, `GigaChatAsyncClient.__init__` добавить `realtime_url: Optional[str] = None` и передавать в `Settings`.

Env var автоматически будет:

```text
GIGACHAT_REALTIME_URL
```

URL resolution:

```python
def resolve_realtime_url(explicit_url: Optional[str], settings: Settings) -> str:
    url = explicit_url or settings.realtime_url
    if not url:
        raise ValueError(
            "realtime_url is required for GigaVoice realtime WebSocket. "
            "Pass url=... to connect() or set GIGACHAT_REALTIME_URL."
        )
    if not url.startswith(("ws://", "wss://")):
        raise ValueError("realtime_url must be an absolute ws:// or wss:// URL")
    return url
```

Не выводить URL из `base_url`, потому что в документах нет точного WebSocket path.

---

## 7. Data model cheat-sheet

Все user-facing модели живут в `gigachat.models.realtime`.

Общий принцип:

- Pydantic модели — пользовательский API.
- protobuf — wire-layer.
- `to_pb()` сериализует user model в `voice_pb2.*`.
- `from_pb()` / `from_pb_response()` парсит server protobuf в user model.
- Не возвращать пользователю `voice_pb2` напрямую.

### 7.1 Base conventions

```python
from enum import Enum
from pydantic import BaseModel, ConfigDict

class RealtimeBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
```

Почему `extra="forbid"`: у realtime много похожих полей, опечатки должны ловиться сразу.

Для doc/proto alias использовать `AliasChoices`:

```python
from pydantic import AliasChoices, Field

force_no_speech: Optional[bool] = Field(
    default=None,
    validation_alias=AliasChoices("force_no_speech", "force_co_speech"),
)
```

### 7.2 Duration mapping

Proto использует `google.protobuf.Duration`. В user API использовать `datetime.timedelta`.

Поля-duration:

- `RealtimeInputAudioSettings.silence_phrases_timeout`
- `RealtimeInputAudioSettings.silence_timeout`
- `RealtimeTriggerGeneration.timeout`
- `RealtimeOutputAudio.audio_duration`

Helpers:

```python
def _timedelta_to_pb(value: Optional[timedelta]) -> Optional[duration_pb2.Duration]: ...
def _timedelta_from_pb(value: duration_pb2.Duration) -> Optional[timedelta]: ...
```

Если duration field в proto пустой/default, возвращать `None`, если возможно отличить. Если нельзя отличить default от explicitly zero, это нормально для MVP.

### 7.3 Enums

Все enum-классы сделать `str, Enum`, чтобы пользователю удобно печатать/сравнивать, а в `to_pb()` мапить на int enum proto.

```python
class RealtimeMode(str, Enum):
    MODE_UNSPECIFIED = "MODE_UNSPECIFIED"
    RECOGNIZE_GIGACHAT_SYNTHESIS = "RECOGNIZE_GIGACHAT_SYNTHESIS"
    GIGACHAT_SYNTHESIS = "GIGACHAT_SYNTHESIS"
    GIGACHAT = "GIGACHAT"  # есть в proto, future-mode
    RECOGNIZE_SYNTHESIS = "RECOGNIZE_SYNTHESIS"
```

Нужные enums:

```text
RealtimeMode
RealtimeOutputModalities
RealtimeAudioEncoding
RealtimeSynthesisContentType
RealtimeTriggerFunctionMode
RealtimeAgeType
RealtimeGenderType
RealtimeEventType
RealtimeOutputType
```

### 7.4 Settings models

Wire: `Settings`.

```python
class RealtimeSettings(RealtimeBaseModel):
    gigachat: Optional[RealtimeGigaChatSettings] = None
    audio: Optional[RealtimeAudioSettings] = None
    context: Optional[RealtimeInitialContext] = None
    disable_vad: Optional[bool] = None
    enable_transcribe_input: Optional[bool] = None
    flags: Optional[List[str]] = None
    output_modalities: Optional[RealtimeOutputModalities] = None
    mode: Optional[RealtimeMode] = None
    voice_call_id: str
    first_speaker: Optional[RealtimeFirstSpeaker] = None
    enable_denoiser: Optional[bool] = None
    enable_prefetch: Optional[bool] = None
    enable_person_identity: Optional[bool] = None
    enable_whisper: Optional[bool] = None
    enable_emotion: Optional[bool] = None
```

Why each field exists:

- `voice_call_id`: обязательный backend session id, нужен для трассировки и reconnect.
- `mode`: выбирает backend pipeline: ASR+GigaChat+TTS, GigaChat+TTS, ASR+TTS.
- `output_modalities`: управляет тем, ждать ли audio, text или оба.
- `audio`: ASR/TTS параметры.
- `gigachat`: параметры текстовой/аудио модели и functions.
- `context`: стартовый текстовый контекст для нового соединения или reconnect.
- `disable_vad`: true означает client-side VAD; тогда клиент обязан слать `speech_start`/`speech_end`.
- `enable_transcribe_input`: включает server event `input_transcription`.
- `enable_prefetch`, `enable_person_identity`, `enable_whisper`, `enable_emotion`: дополнительные ASR detections; backend требует `enable_transcribe_input=True`.
- `first_speaker`: позволяет модели начать первой.
- `flags`: feature flags.

Validation:

- Проверять, что `voice_call_id` похож на UUID v4/UUID string. Минимум — `uuid.UUID(value)`.
- Не валидировать backend-only совместимость всех режимов слишком жёстко в SDK. Например, backend сам скажет, если `enable_whisper` не совместим с mode.
- Можно добавить soft validation: если detection flags включены, а `enable_transcribe_input` не true, выбросить `ValueError`, потому что документ явно говорит, что backend вернёт ошибку.

### 7.5 Audio settings

Wire:

```text
AudioSettings.input  -> Input
AudioSettings.output -> Output
```

User models:

```python
class RealtimeAudioSettings(RealtimeBaseModel):
    input: Optional[RealtimeInputAudioSettings] = None
    output: Optional[RealtimeOutputAudioSettings] = None

class RealtimeInputAudioSettings(RealtimeBaseModel):
    model: Optional[str] = None
    audio_encoding: Optional[RealtimeAudioEncoding] = None
    sample_rate: Optional[int] = None
    silence_phrases: Optional[List[str]] = None
    silence_phrases_timeout: Optional[timedelta] = None
    silence_timeout: Optional[timedelta] = None
    stop_phrases: Optional[List[str]] = None
    ignore_phrases: Optional[List[str]] = None

class RealtimeOutputAudioSettings(RealtimeBaseModel):
    voice: Optional[str] = None
    audio_encoding: Optional[RealtimeAudioEncoding] = None
    stub_sounds: Optional[RealtimeStubSounds] = None
```

Why:

- `input` отвечает за распознавание и тишину.
- `output` отвечает за синтез и звуковые заглушки.
- Если `audio.input`/`audio.output` не заданы, backend выбирает defaults.

### 7.6 Stub sounds

Proto:

```text
StubSounds.trigger_delay     = 1
StubSounds.trigger_function  = 2
StubSounds.sounds            = 3
```

Doc говорит `trigger_generation`, proto говорит `trigger_delay`. User-facing canonical name должен быть `trigger_generation`, потому что это понятнее и совпадает с бизнес-смыслом, но `trigger_delay` принимать как alias.

```python
class RealtimeStubSounds(RealtimeBaseModel):
    trigger_generation: Optional[RealtimeTriggerGeneration] = Field(
        default=None,
        validation_alias=AliasChoices("trigger_generation", "trigger_delay"),
    )
    trigger_function: Optional[RealtimeTriggerFunction] = None
    sounds: Optional[List[str]] = None
```

`to_pb()` должен писать `trigger_delay`.

### 7.7 GigaChat settings

Wire: `GigaChatSettings`.

```python
class RealtimeGigaChatSettings(RealtimeBaseModel):
    model: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    repetition_penalty: Optional[float] = None
    update_interval: Optional[float] = None  # есть в proto
    profanity_check: Optional[bool] = None
    filters_settings: Optional[Dict[str, RealtimeFilterSettings]] = None
    functions: Optional[List[RealtimeFunction]] = None
    function_registry: Optional[RealtimeFunctionRegistry] = None
    filter_stub_phrases: Optional[List[str]] = None
    current_time: Optional[int] = None
    function_ranker: Optional[RealtimeFunctionRanker] = None
```

Why:

- `model`, sampling params, `profanity_check` — параметры генерации GigaChat.
- `functions` — клиентские функции, которые backend может вызвать через server event `function_call`.
- `function_registry` — параметры function registry.
- `filter_stub_phrases` — замены фильтр-заглушек для синтеза.
- `current_time` — нужен для сценариев поиска/get_datetime.
- `function_ranker` — backend ранжирует functions перед отправкой в модель.

Doc/proto alias:

```python
class RealtimeFunctionRanker(RealtimeBaseModel):
    enable: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("enable", "enabled"),
    )
    top_n: Optional[int] = None
```

`to_pb()` должен писать `enabled`.

### 7.8 Functions

Wire: `Function`, `AnyExample`, `Params`, `Pair`, `FunctionRegistry`.

```python
class RealtimeFunction(RealtimeBaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[str] = None
    few_shot_examples: Optional[List[RealtimeAnyExample]] = None
    return_parameters: Optional[str] = None
```

Important:

- `parameters` и `return_parameters` в proto — строки с JSON Schema, не dict.
- Можно в helper later разрешить dict, но MVP — string only.

### 7.9 Context models

Wire: `InitialContext`, `Message`, `FunctionCall`.

```python
class RealtimeInitialContext(RealtimeBaseModel):
    messages: List[RealtimeMessage]

class RealtimeMessage(RealtimeBaseModel):
    role: str
    content: str
    function_call: Optional[RealtimeFunctionCall] = None
    function_name: Optional[str] = None
    functions_state_id: Optional[str] = None
    attachments: Optional[List[str]] = None
    inline_data: Optional[Dict[str, str]] = None
```

Why:

- Нужен для старта диалога со стороны модели и reconnect.
- SDK не должен сам пересобирать контекст в MVP.
- Не добавлять `functions` в `RealtimeMessage`, потому что в текущем proto такого поля нет, хотя Word-документ его упоминает.

### 7.10 Client request models

Wire root: `GigaVoiceRequest` oneof:

```text
settings        = 1
input           = 2
function_result = 3
```

User-facing можно сделать через отдельные models + helper methods session. Не обязательно заставлять пользователя вручную создавать `RealtimeClientEvent`.

```python
class RealtimeAudioContent(RealtimeBaseModel):
    audio_chunk: Optional[bytes] = None
    speech_start: Optional[bool] = None
    speech_end: Optional[bool] = None
    meta: Optional[RealtimeAudioChunkMeta] = None

class RealtimeAudioChunkMeta(RealtimeBaseModel):
    force_no_speech: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("force_no_speech", "force_co_speech"),
    )

class RealtimeSynthesisContent(RealtimeBaseModel):
    text: str
    content_type: RealtimeSynthesisContentType = RealtimeSynthesisContentType.TEXT
    is_final: Optional[bool] = None

class RealtimeFunctionResult(RealtimeBaseModel):
    content: str
    function_name: Optional[str] = None
```

Doc/proto alias:

- Document says `input.synthesis_content`.
- Proto says `ContentFromClient.content_for_synthesis`.
- User-facing helper/method should be `send_synthesis(...)` and model name `RealtimeSynthesisContent`.
- `to_pb()` must write `content_for_synthesis`.

`send_function_result` convenience:

```python
if isinstance(content, dict):
    content = json.dumps(content, ensure_ascii=False)
```

### 7.11 Server event models

Wire root: `GigaVoiceResponse` oneof:

```text
output               = 1
function_call        = 2
input_transcription  = 3
output_transcription = 4
error                = 5
warning              = 6
input_files          = 7
```

User-facing root:

```python
class RealtimeServerEvent(RealtimeBaseModel):
    output: Optional[RealtimeOutput] = None
    function_call: Optional[RealtimeFunctionCalling] = None
    input_transcription: Optional[RealtimeInputTranscription] = None
    output_transcription: Optional[RealtimeOutputTranscription] = None
    error: Optional[RealtimeError] = None
    warning: Optional[RealtimeWarning] = None
    input_files: Optional[RealtimeInputFiles] = None

    @property
    def type(self) -> RealtimeEventType: ...
```

Do not raise automatically on `error` in MVP. Yield `RealtimeServerEvent(error=...)`; the server may close after that.

#### `RealtimeOutput`

Wire: `ContentFromModel` oneof:

```text
audio           = 1
additional_data = 2
interrupted     = 3
```

```python
class RealtimeOutput(RealtimeBaseModel):
    audio: Optional[RealtimeOutputAudio] = None
    additional_data: Optional[RealtimeAdditionalData] = None
    interrupted: Optional[bool] = None

    @property
    def type(self) -> RealtimeOutputType: ...
```

Why:

- `audio` carries TTS chunks.
- `additional_data` carries usage/model/finish reason.
- `interrupted=True` tells client to stop current playback/rendering.

#### `RealtimeOutputAudio`

```python
class RealtimeOutputAudio(RealtimeBaseModel):
    audio_chunk: bytes
    audio_duration: Optional[timedelta] = None
    is_final: Optional[bool] = None
```

`is_final=True` means current audio generation is complete.

#### `RealtimeAdditionalData`

```python
class RealtimeAdditionalData(RealtimeBaseModel):
    usage: Optional[RealtimeUsage] = None
    gigachat_model_info: Optional[RealtimeGigaChatModelInfo] = None
    finish_reason: Optional[str] = None
```

#### `RealtimeFunctionCalling`

```python
class RealtimeFunctionCalling(RealtimeBaseModel):
    function_call: RealtimeFunctionCall
    timestamp: int
```

When received, SDK does not execute the function. User code executes it and calls `send_function_result(...)`.

#### `RealtimeInputTranscription`

```python
class RealtimeInputTranscription(RealtimeBaseModel):
    text: str
    timestamp: int
    unnormalized_text: Optional[str] = None
    person_identity: Optional[RealtimePersonIdentity] = None
    prefetch: Optional[bool] = None
    whisper: Optional[bool] = None
    emotion: Optional[RealtimeEmotion] = None
```

Why:

- Contains recognized user speech.
- Additional fields appear only when settings enable corresponding ASR detections.

#### `RealtimeOutputTranscription`

Proto fields:

```text
text               = 1
functions_state_id = 2
finish_reason      = 3
timestamp          = 4
stub_text          = 5
inline_data        = 6
```

```python
class RealtimeOutputTranscription(RealtimeBaseModel):
    text: str
    functions_state_id: Optional[str] = None
    finish_reason: Optional[str] = None
    timestamp: int
    stub_text: Optional[str] = None
    inline_data: Optional[Dict[str, str]] = None
```

Important gap:

- Word-документ описывает `silence_phrase`, но в proto его нет.
- Не добавлять это поле в wire model до обновления proto.

#### `RealtimeInputFiles`

```python
class RealtimeInputFile(RealtimeBaseModel):
    id: str
    type: str

class RealtimeInputFiles(RealtimeBaseModel):
    files: List[RealtimeInputFile]
```

Needed for `GIGACHAT_SYNTHESIS`, where backend returns uploaded audio file ids for context/reconnect.

#### `RealtimeError` и `RealtimeWarning`

```python
class RealtimeError(RealtimeBaseModel):
    status: int
    message: str

class RealtimeWarning(RealtimeBaseModel):
    message: str
```

`error` is blocking by business semantics, but SDK should expose it as event in MVP.
`warning` is non-blocking.

---

## 8. Proto/doc mismatch table

Codex must include this table in `docs/internal/RESOURCE_REALTIME_PROGRESS.md` initially and keep it updated if proto changes.

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

---

## 9. Progress protocol

Create `docs/internal/RESOURCE_REALTIME_PROGRESS.md` in slice 01.

Each slice must append/update one block:

```md
## Slice NN — <commit message>

Status: not_started | in_progress | done | blocked
Date: YYYY-MM-DD

### Goal
<one sentence>

### Done in this slice
- ...

### Files changed
- ...

### Tests run
- `uv run pytest ...` — passed/failed/not run, reason
- `uv run ruff check .` — passed/failed/not run, reason
- `make mypy` — passed/failed/not run, reason

### Notes / blockers
- ...

### Next slice
Slice NN+1 — <name>. Do not start it in the current run.
```

Rules:

- At the start of each task, mark current slice `in_progress`.
- Before commit, mark it `done` or `blocked`.
- Do not mark future slices done.
- If tests cannot run because dependency is unavailable, write that explicitly.
- Every commit must include the progress-file update.

---

## 10. Commit-срезы

### Slice 01 — `docs(realtime): add resource realtime codex plan`

One task: put this plan into the repo and create progress tracking.

Files:

```text
docs/internal/RESOURCE_REALTIME_CODEX_PLAN.md
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

- Copy this markdown plan into `docs/internal/RESOURCE_REALTIME_CODEX_PLAN.md`.
- Create `RESOURCE_REALTIME_PROGRESS.md`.
- Add gap table from section 8.
- Mark Slice 01 as `done`.

Do not implement code.

Acceptance:

```bash
git diff --check
```

Commit and stop.

---

### Slice 02 — `chore(realtime): add websocket realtime settings and extras`

One task: add configuration/dependency plumbing only.

Files:

```text
pyproject.toml
src/gigachat/settings.py
src/gigachat/client.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

- Add optional extra `realtime = ["protobuf>=4,<6", "websockets>=12,<16"]`.
- Add `realtime_url: Optional[str]` to `Settings`.
- Add `realtime_url` constructor arg to sync and async clients and `_BaseClient`.
- Pass `realtime_url` into `Settings`.

Do not:

- Add `grpcio`.
- Add realtime resources yet.
- Add proto/models yet.

Acceptance:

```bash
uv run pytest tests/unit/gigachat/test_client.py  # or nearest existing client settings tests
uv run ruff check src/gigachat/settings.py src/gigachat/client.py
make mypy
```

If exact test path differs, run nearest relevant tests and record in progress.

Commit and stop.

---

### Slice 03 — `feat(realtime): add GigaVoice protobuf bindings`

One task: add proto and generated Python binding, without SDK models.

Files:

```text
src/gigachat/proto/__init__.py
src/gigachat/proto/gigavoice/__init__.py
src/gigachat/proto/gigavoice/voice.proto
src/gigachat/proto/gigavoice/voice_pb2.py
tests/unit/gigachat/proto/test_gigavoice_proto.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

- Copy source `voice.proto` into package.
- Generate `voice_pb2.py` only.
- Add a tiny test that imports `voice_pb2` when protobuf is installed and verifies root message names exist:
  - `GigaVoiceRequest`
  - `GigaVoiceResponse`
  - `Settings`
  - `ContentFromClient`
  - `ContentFromModel`

Do not:

- Generate `voice_pb2_grpc.py`.
- Add `grpcio`.
- Add transport.

Acceptance:

```bash
uv run pytest tests/unit/gigachat/proto/test_gigavoice_proto.py
uv run ruff check src/gigachat/proto tests/unit/gigachat/proto
make mypy
```

Commit and stop.

---

### Slice 04 — `feat(realtime): add settings models and protobuf serialization`

One task: add only settings-side data models and `RealtimeSettings.to_pb()`.

Files:

```text
src/gigachat/models/realtime.py
src/gigachat/models/__init__.py
tests/unit/gigachat/models/test_realtime_settings.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement models from sections:

- `RealtimeBaseModel`
- enums needed by settings
- `RealtimeSettings`
- `RealtimeAudioSettings`
- `RealtimeInputAudioSettings`
- `RealtimeOutputAudioSettings`
- `RealtimeStubSounds`
- `RealtimeTriggerGeneration`
- `RealtimeTriggerFunction`
- `RealtimeGigaChatSettings`
- `RealtimeFilterSettings`
- `RealtimeFunction`
- `RealtimeFunctionRegistry`
- `RealtimeFunctionRanker`
- `RealtimeInitialContext`
- `RealtimeMessage`
- `RealtimeFirstSpeaker`
- `RealtimeFunctionCall`
- duration helpers

Implement:

- `RealtimeSettings.to_pb()`.
- Nested `to_pb()` helpers as needed.
- Alias handling:
  - `FunctionRanker.enable` -> proto `enabled`.
  - `StubSounds.trigger_generation` -> proto `trigger_delay`.
- `voice_call_id` UUID validation.

Do not:

- Add request input models.
- Add server response models.
- Add WebSocket.

Acceptance tests:

- Minimal settings serializes to `voice_pb2.Settings`.
- Full audio settings serializes enum/duration fields.
- `FunctionRanker(enable=True)` writes `enabled=True`.
- `StubSounds(trigger_generation=...)` writes `trigger_delay`.
- Invalid `voice_call_id` raises validation error.
- Import `gigachat.models.realtime` without importing `voice_pb2` at module import, if feasible.

Commit and stop.

---

### Slice 05 — `feat(realtime): add client request models`

One task: add client request/event models and protobuf serialization.

Files:

```text
src/gigachat/models/realtime.py
tests/unit/gigachat/models/test_realtime_requests.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

- `RealtimeAudioContent`
- `RealtimeAudioChunkMeta`
- `RealtimeSynthesisContent`
- `RealtimeFunctionResult`
- optional `RealtimeClientEvent` / `RealtimeClientRequest` wrapper if useful
- serialization helpers to `voice_pb2.GigaVoiceRequest`:
  - settings request
  - audio input request
  - synthesis input request
  - function result request

Alias handling:

- `AudioChunkMeta.force_no_speech` accepts alias `force_co_speech`.
- user-facing synthesis maps to proto `content_for_synthesis`.

Convenience:

- `RealtimeFunctionResult.from_content(content, function_name=None)` may accept dict and JSON-dump it.

Do not:

- Add server response parsing.
- Add WebSocket.

Acceptance tests:

- Audio request sets `input.audio_content.audio_chunk`.
- Speech flags round into proto.
- Alias `force_co_speech=True` writes proto `force_no_speech=True`.
- Synthesis request writes `content_for_synthesis`, content type TEXT/SSML.
- Function result request writes valid JSON string when dict is passed.
- Serialized payload size can be checked by helper, but enforcement can wait until transport slice.

Commit and stop.

---

### Slice 06 — `feat(realtime): add server event models`

One task: parse protobuf server responses into user-facing Pydantic events.

Files:

```text
src/gigachat/models/realtime.py
tests/unit/gigachat/models/test_realtime_responses.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

- `RealtimeServerEvent`
- `RealtimeOutput`
- `RealtimeOutputAudio`
- `RealtimeAdditionalData`
- `RealtimeUsage`
- `RealtimeGigaChatModelInfo`
- `RealtimeFunctionCalling`
- `RealtimeInputTranscription`
- `RealtimePersonIdentity`
- `RealtimeEmotion`
- `RealtimeOutputTranscription`
- `RealtimeInputFiles`
- `RealtimeInputFile`
- `RealtimeError`
- `RealtimeWarning`
- `RealtimeEventType`
- `RealtimeOutputType`
- `from_pb_response()` parser

Do not:

- Add WebSocket.
- Add `silence_phrase`; not in proto.
- Add `platform_function_processing`; not in proto.

Acceptance tests:

- Each `GigaVoiceResponse.oneof` variant parses correctly.
- `ContentFromModel` variants parse correctly:
  - audio
  - additional_data
  - interrupted
- `.type` property returns expected event type.
- `.output.type` returns expected output type.
- Duration parses to `timedelta`.
- Unknown/empty oneof raises clear `ValueError` or returns type `unknown` if you explicitly design that; prefer clear `ValueError`.

Commit and stop.

---

### Slice 07 — `feat(realtime): add websocket payload utilities`

One task: add low-level WebSocket protobuf framing helpers, no public resource yet.

Files:

```text
src/gigachat/api/realtime.py
tests/unit/gigachat/api/test_realtime_payloads.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

- `MAX_REALTIME_MESSAGE_BYTES = 4 * 1024 * 1024`.
- `serialize_realtime_request(request: voice_pb2.GigaVoiceRequest) -> bytes`.
- `parse_realtime_response(data: Union[bytes, bytearray]) -> RealtimeServerEvent`.
- `_ensure_realtime_dependencies()` or separate lazy import helpers.
- `resolve_realtime_url(explicit_url, settings)`.
- Payload size validation: raise `ValueError` before send if serialized request > 4 MB.

Do not:

- Open real WebSocket.
- Add resources.

Acceptance tests:

- Serialization returns bytes.
- Oversized message raises.
- Parsing binary response returns `RealtimeServerEvent`.
- Missing realtime URL raises clear `ValueError`.
- Non-ws/wss URL raises.

Commit and stop.

---

### Slice 08 — `feat(realtime): add async websocket session`

One task: implement async session object that opens WebSocket, sends settings first, sends/receives events.

Files:

```text
src/gigachat/api/realtime.py
tests/unit/gigachat/api/test_realtime_async_websocket.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

```python
class AsyncRealtimeSession:
    def __init__(self, base_client, settings, url=None): ...
    async def __aenter__(self) -> "AsyncRealtimeSession": ...
    async def __aexit__(self, *exc): ...
    async def open(self) -> None: ...
    async def close(self) -> None: ...
    async def send_request(self, request) -> None: ...
    async def send_audio(...): ...
    async def send_synthesis(...): ...
    async def send_function_result(...): ...
    async def receive(self) -> RealtimeServerEvent: ...
    def __aiter__(self): ...
    async def __anext__(self): ...
```

Auth/header requirements:

- Before opening, ensure token is available using async client auth path.
- Build headers with existing `build_headers(access_token)`.
- Include context headers through `build_headers`.
- On WebSocket handshake 401/auth failure, refresh token once and retry once.

WebSocket behavior:

- Use `websockets` lazy import.
- First binary message after successful open must be `settings` request.
- Send each request as one binary WebSocket message containing serialized `GigaVoiceRequest`.
- Receive binary messages and parse as `GigaVoiceResponse`.
- If text frame arrives, raise clear error because protocol is binary protobuf.

Do not:

- Add sync session.
- Add public client resource yet.

Acceptance tests with fake/mocked websockets:

- `__aenter__` opens connection and sends settings first.
- Headers include `Authorization` when token exists.
- `send_audio` sends binary protobuf input.
- `receive` parses binary protobuf response.
- `async for` yields events.
- `close` closes WebSocket.
- Missing optional dependency raises helpful ImportError.

Commit and stop.

---

### Slice 09 — `feat(resources): expose async realtime resource`

One task: add `client.a_realtime` Resource API namespace.

Files:

```text
src/gigachat/resources/realtime.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_realtime_resources.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

```python
class RealtimeAsyncResource:
    def __init__(self, base_client: "GigaChatAsyncClient") -> None: ...

    def connect(
        self,
        settings: Union[RealtimeSettings, Dict[str, Any]],
        *,
        url: Optional[str] = None,
    ) -> AsyncRealtimeSession:
        ...
```

Add to async client:

```python
@cached_property
def a_realtime(self) -> RealtimeAsyncResource:
    return RealtimeAsyncResource(self)
```

Do not:

- Add sync resource.
- Add root shim.

Acceptance tests:

- `client.a_realtime` exists and is cached.
- `client.a_realtime.connect(dict_settings)` validates into `RealtimeSettings`.
- No `DeprecationWarning`.
- `import gigachat` works without optional realtime dependency as long as connect/open is not called.

Commit and stop.

---

### Slice 10 — `feat(realtime): add sync websocket session`

One task: implement sync session object.

Files:

```text
src/gigachat/api/realtime.py
tests/unit/gigachat/api/test_realtime_sync_websocket.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement sync equivalent:

```python
class SyncRealtimeSession:
    def __enter__(self) -> "SyncRealtimeSession": ...
    def __exit__(self, *exc): ...
    def open(self) -> None: ...
    def close(self) -> None: ...
    def send_request(self, request) -> None: ...
    def send_audio(...): ...
    def send_synthesis(...): ...
    def send_function_result(...): ...
    def receive(self) -> RealtimeServerEvent: ...
    def __iter__(self): ...
    def __next__(self): ...
```

Use `websockets.sync.client.connect` if available in the selected `websockets` range.

Auth/header requirements mirror async:

- Ensure token before open.
- Build headers with `build_headers`.
- Retry once on handshake auth failure.

Do not:

- Add sync resource yet.

Acceptance tests:

- `__enter__` opens and sends settings first.
- `send_audio` sends binary protobuf input.
- `receive` parses response.
- Iterator yields events.
- Missing dependency raises helpful ImportError.

Commit and stop.

---

### Slice 11 — `feat(resources): expose sync realtime resource`

One task: add `client.realtime` Resource API namespace.

Files:

```text
src/gigachat/resources/realtime.py
src/gigachat/resources/__init__.py
src/gigachat/client.py
tests/unit/gigachat/test_client_realtime_resources.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

```python
class RealtimeSyncResource:
    def __init__(self, base_client: "GigaChatSyncClient") -> None: ...

    def connect(
        self,
        settings: Union[RealtimeSettings, Dict[str, Any]],
        *,
        url: Optional[str] = None,
    ) -> SyncRealtimeSession:
        ...
```

Add to sync client:

```python
@cached_property
def realtime(self) -> RealtimeSyncResource:
    return RealtimeSyncResource(self)
```

Do not:

- Add root shim.
- Add gRPC.

Acceptance tests:

- `client.realtime` exists and is cached.
- `client.realtime.connect(dict_settings)` validates settings.
- No deprecation warnings.

Commit and stop.

---

### Slice 12 — `feat(realtime): add audio chunk validation helpers`

One task: add SDK-side validation for limits that can be checked locally.

Files:

```text
src/gigachat/api/realtime.py
src/gigachat/models/realtime.py
tests/unit/gigachat/api/test_realtime_audio_validation.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

- Keep hard validation: serialized message <= 4 MB.
- Add optional/soft duration validation for known mono encodings:
  - `PCM_S16LE`: 2 bytes per sample.
  - `PCM_ALAW`: 1 byte per sample.
  - Need `sample_rate` from session settings.
- If known encoding and chunk is longer than 2 seconds, raise `ValueError` before sending.
- For `OPUS`, do not estimate duration; only validate message size.

Do not:

- Decode audio.
- Add external audio libraries.

Acceptance tests:

- PCM_S16LE 16kHz chunk of 64000 bytes is accepted as 2 seconds.
- PCM_S16LE 16kHz chunk > 64000 bytes raises.
- OPUS only checks message size.

Commit and stop.

---

### Slice 13 — `docs(realtime): add websocket realtime examples`

One task: add examples and README docs.

Files:

```text
README.md
MIGRATION_GUIDE.md
MIGRATION_GUIDE_ru.md
examples/example_realtime_voice.py
examples/example_realtime_synthesis_only.py
examples/example_realtime_text_output.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Document:

- Install:

```bash
pip install "gigachat[realtime]"
```

- Async example for `RECOGNIZE_GIGACHAT_SYNTHESIS`.
- Sync example if sync resource is already implemented.
- `RECOGNIZE_SYNTHESIS` example with `send_synthesis`.
- `TEXT` output example.
- Explain `voice_call_id` and reconnect: preserve same id for same call, but manually pass context.
- Explain `output.interrupted` and `output.audio.is_final`.
- Explain no gRPC support in SDK.

Do not:

- Add microphone/playback dependencies.
- Use endpoint guesses. Examples should read URL from `GIGACHAT_REALTIME_URL`.

Acceptance:

```bash
uv run ruff check examples
```

Commit and stop.

---

### Slice 14 — `test(realtime): add opt-in integration smoke test`

One task: add integration test marker for real service, disabled by default.

Files:

```text
tests/integration/test_realtime_websocket.py
pyproject.toml  # only if a new marker is needed
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Implement:

- Marker: `realtime_integration` or reuse `integration` if maintainers prefer.
- Test should skip unless env vars are set:

```text
GIGACHAT_REALTIME_URL
GIGACHAT_CREDENTIALS or GIGACHAT_ACCESS_TOKEN
```

- Smoke test should open WS, send settings, then close. Do not require microphone/audio fixture unless a tiny silence PCM fixture is committed intentionally.

Do not:

- Run by default.
- Depend on real endpoint in unit tests.

Acceptance:

```bash
uv run pytest -m realtime_integration
uv run pytest
```

Commit and stop.

---

### Slice 15 — `chore(realtime): finalize realtime resource progress`

One task: final cleanup and audit.

Files:

```text
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Plus any tiny cleanup files found during audit.

Checklist:

```bash
uv run pytest
uv run ruff check .
make mypy
git diff --check
```

No gRPC audit:

```bash
git grep -n "grpcio\|pb2_grpc\|transport=.*grpc" -- ':!docs/internal/RESOURCE_REALTIME_CODEX_PLAN.md' ':!docs/internal/RESOURCE_REALTIME_PROGRESS.md'
```

Expected: no runtime/code matches.

Optional dependency audit:

- `import gigachat` works without realtime extra.
- `client.realtime` and `client.a_realtime` properties can be accessed without opening connection.
- Calling `.connect(...).__enter__()` / `.__aenter__()` without extra raises helpful ImportError.

Commit and stop.

---

## 11. Implementation notes for WebSocket transport

### 11.1 Headers

Use existing `build_headers(access_token)` from `gigachat.api.utils`.

This preserves:

- `Authorization`
- `User-Agent`
- `X-Session-ID`
- `X-Request-ID`
- `X-Service-ID`
- `X-Operation-ID`
- `X-Client-ID`
- `X-Trace-ID`
- `X-Agent-ID`
- custom headers

Do not overwrite context `X-Session-ID` with `voice_call_id`. Backend uses `voice_call_id` inside protobuf settings for tracing; headers remain SDK context headers.

### 11.2 Auth retry

Pseudo:

```python
async def _open_once(self):
    await self._base_client._aupdate_token()
    headers = build_headers(self._base_client.token)
    self._ws = await websockets.connect(self._url, extra_headers=headers, ...)

async def open(self):
    try:
        await self._open_once()
    except websocket_auth_error:
        self._base_client._reset_token()
        await self._base_client._aupdate_token()
        await self._open_once()
    await self.send_request(RealtimeClientRequest.settings(self._settings))
```

For sync use `_update_token()`.

The exact exception class differs between `websockets` versions (`InvalidStatus`, `InvalidStatusCode`). Tests should not depend too tightly on class internals; wrap status detection in helper.

### 11.3 Binary framing

Each WebSocket message is exactly one serialized `GigaVoiceRequest` or `GigaVoiceResponse`.

No length prefix.

If backend later requires length-prefix, this must be changed only after backend confirmation.

### 11.4 Session state

Track:

```python
self._opened: bool
self._closed: bool
self._ws: Optional[...]
self._settings: RealtimeSettings
```

Raise clear errors:

- Sending before open.
- Receiving before open.
- Opening twice.
- Sending after close.

### 11.5 Iteration

Async:

```python
def __aiter__(self):
    return self

async def __anext__(self):
    try:
        return await self.receive()
    except ConnectionClosed:
        raise StopAsyncIteration
```

Sync equivalent with `StopIteration`.

Do not swallow `RealtimeError` event: if server sends an error protobuf and then closes, yield the error event first.

---

## 12. Testing strategy

### 12.1 Unit tests only with fake WebSocket

Do not hit real network in unit tests.

Fake object shape:

```python
class FakeAsyncWebSocket:
    sent: List[bytes]
    incoming: asyncio.Queue[Union[bytes, str]]

    async def send(self, data): ...
    async def recv(self): ...
    async def close(self): ...
```

For sync, simple list/iterator fake.

Patch `websockets.connect` / `websockets.sync.client.connect` to return fake.

### 12.2 Model tests

Use `voice_pb2` directly in tests to build pb messages and verify mappings.

Test every oneof branch explicitly.

### 12.3 Import tests

Have a test that simulates missing optional dependencies only if feasible without brittle monkeypatching.

At minimum, code should have lazy import helpers and targeted tests for error message.

### 12.4 Full checks

Final slice should run:

```bash
uv run pytest
uv run ruff check .
make mypy
git diff --check
```

---

## 13. Non-goals

Do not implement in this SDK work:

- gRPC transport.
- Automatic reconnect and context reconstruction.
- Microphone capture.
- Speaker playback.
- Audio transcoding/decoding.
- Backend business logic for VAD/interruption/dogovarivanie.
- Platform function processing event until proto is updated.
- `disable_interruption` until proto is updated.
- `silence_phrase` until proto is updated.
- Hardcoded WebSocket endpoint.

---

## 14. Suggested final API exports

In `gigachat.models.realtime.__all__` export:

```python
__all__ = (
    "RealtimeAdditionalData",
    "RealtimeAgeType",
    "RealtimeAudioChunkMeta",
    "RealtimeAudioContent",
    "RealtimeAudioEncoding",
    "RealtimeAudioSettings",
    "RealtimeEmotion",
    "RealtimeError",
    "RealtimeEventType",
    "RealtimeFilterSettings",
    "RealtimeFirstSpeaker",
    "RealtimeFunction",
    "RealtimeFunctionCall",
    "RealtimeFunctionCalling",
    "RealtimeFunctionRanker",
    "RealtimeFunctionRegistry",
    "RealtimeFunctionResult",
    "RealtimeGenderType",
    "RealtimeGigaChatModelInfo",
    "RealtimeGigaChatSettings",
    "RealtimeInitialContext",
    "RealtimeInputAudioSettings",
    "RealtimeInputFile",
    "RealtimeInputFiles",
    "RealtimeInputTranscription",
    "RealtimeMessage",
    "RealtimeMode",
    "RealtimeOutput",
    "RealtimeOutputAudio",
    "RealtimeOutputAudioSettings",
    "RealtimeOutputModalities",
    "RealtimeOutputTranscription",
    "RealtimeOutputType",
    "RealtimePersonIdentity",
    "RealtimeServerEvent",
    "RealtimeSettings",
    "RealtimeStubSounds",
    "RealtimeSynthesisContent",
    "RealtimeSynthesisContentType",
    "RealtimeTriggerFunction",
    "RealtimeTriggerFunctionMode",
    "RealtimeTriggerGeneration",
    "RealtimeUsage",
    "RealtimeWarning",
)
```

In `gigachat.resources.__init__` export:

```python
RealtimeAsyncResource
RealtimeSyncResource
```

---

## 15. Commit message style

Use concise conventional commits:

```text
docs(realtime): add resource realtime codex plan
chore(realtime): add websocket realtime settings and extras
feat(realtime): add GigaVoice protobuf bindings
feat(realtime): add settings models and protobuf serialization
feat(realtime): add client request models
feat(realtime): add server event models
feat(realtime): add websocket payload utilities
feat(realtime): add async websocket session
feat(resources): expose async realtime resource
feat(realtime): add sync websocket session
feat(resources): expose sync realtime resource
docs(realtime): add websocket realtime examples
test(realtime): add opt-in integration smoke test
chore(realtime): finalize realtime resource progress
```

Every commit should mention progress in body if useful:

```text
Progress: docs/internal/RESOURCE_REALTIME_PROGRESS.md updated for Slice NN.
```

---

## 16. First prompt to give Codex

Use this exact instruction when starting Codex:

```text
You are on branch feature/resource-api-non-chat.
Read docs/internal/RESOURCE_REALTIME_CODEX_PLAN.md and docs/internal/RESOURCE_REALTIME_PROGRESS.md.
Take exactly one unfinished slice: the first one whose Status is not done.
Do not start the next slice.
Update docs/internal/RESOURCE_REALTIME_PROGRESS.md at the start and end of the slice.
Commit exactly one commit using the commit message specified for the slice.
Do not add gRPC support, grpcio, pb2_grpc, or transport="grpc".
Stop after the commit and report changed files and tests run.
```
