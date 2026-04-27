# План реализации `resource realtime` для `gigachat`: WebSocket + JSON events, без gRPC и protobuf

Документ предназначен для GPT-5.5 Codex, который будет работать в ветке `feature/resource-api-non-chat` из PR #110.

Этот план **заменяет предыдущий protobuf-план**. Теперь целевой SDK-контракт такой:

```python
client.realtime      # sync Resource API namespace
client.a_realtime    # async Resource API namespace
```

Транспорт: **только WebSocket**.

Wire-format: **UTF-8 JSON frames**.

Audio payload: **base64 string внутри JSON**, потому что без protobuf нельзя передать `bytes` как бинарное поле в typed event object.

Optional audio helpers: `sounddevice` + `numpy`.

API-стиль: ориентироваться на `openai-python` Realtime API:

- `client.realtime.connect(...)` возвращает context manager;
- `async with client.a_realtime.connect(...) as connection: ...`;
- `async for event in connection: ...`;
- `connection.send(...)`, `connection.recv()`, `connection.send_raw(...)`, `connection.parse_event(...)`;
- event handlers: `.on(...)`, `.off(...)`, `.once(...)`, `.dispatch_events()`;
- request params — typed dictionaries;
- response/server events — Pydantic models.

---

## 0. Самое важное перед кодингом

### 0.1. Контрактный риск

Word-документ GigaVoice описывает WebSocket `внутри protobuf`. В этом плане protobuf запрещён. Значит Codex должен реализовывать **JSON-over-WebSocket SDK** и явно зафиксировать в progress-файле:

> Требуется backend JSON WebSocket endpoint или JSON gateway. Если текущий endpoint принимает только protobuf frames, этот SDK-план не сможет пройти integration smoke test без backend-адаптера.

Не пытаться “частично” использовать `voice.proto`. Не генерировать `*_pb2.py`. Не импортировать `google.protobuf`. Не коммитить `voice.proto` в SDK.

### 0.2. Почему JSON events

Мы хотим API ближе к OpenAI Realtime: события имеют строковый `type`, сериализуются в JSON, серверные события парсятся в Pydantic-модели, пользователь может работать через iterator или через callbacks.

Пример желаемого SDK API:

```python
from uuid import uuid4

from gigachat import GigaChat
from gigachat.types.realtime import RealtimeSettingsParam

settings: RealtimeSettingsParam = {
    "voice_call_id": str(uuid4()),
    "mode": "RECOGNIZE_GIGACHAT_SYNTHESIS",
    "output_modalities": "AUDIO_TEXT",
    "enable_transcribe_input": True,
    "audio": {
        "input": {"audio_encoding": "PCM_S16LE", "sample_rate": 16000},
        "output": {"audio_encoding": "PCM_S16LE"},
    },
}

async with GigaChat(credentials="...") as client:
    async with client.a_realtime.connect(settings=settings, url="wss://...") as connection:
        await connection.input_audio.send(chunk, speech_start=True)

        async for event in connection:
            if event.type == "input_transcription":
                print(event.text)

            elif event.type == "output.audio":
                await speaker.write(event.audio_chunk)
                if event.is_final:
                    break

            elif event.type == "output.interrupted":
                speaker.stop()

            elif event.type == "error":
                print(event.status, event.message)
                break
```

---

## 1. Жёсткие правила для Codex

1. **Нельзя брать больше одной задачи за один заход.**
   - Выбери первый незавершённый slice из раздела `12. Commit-срезы`.
   - Сделай только его.
   - Сделай один commit.
   - Остановись и отчитайся.

2. **Каждый slice обязан обновлять progress-файл.**
   - Progress-файл в репозитории: `docs/internal/RESOURCE_REALTIME_PROGRESS.md`.
   - В каждом commit должен быть diff этого файла.
   - Формат записи см. раздел `11. Progress protocol`.

3. **gRPC запрещён.**
   - Не добавлять `grpcio`, `grpcio-tools`.
   - Не добавлять `transport="grpc"`.
   - Не создавать gRPC transport, channel, stub, service client.

4. **protobuf запрещён.**
   - Не добавлять `protobuf` dependency.
   - Не генерировать `voice_pb2.py`.
   - Не импортировать `google.protobuf`.
   - Не использовать `voice.proto` как источник runtime-кода.
   - Не добавлять length-prefix framing.

5. **Wire-format — только JSON.**
   - `websockets.send()` отправляет `str`, полученный из `json.dumps(...)`.
   - `websockets.recv()` ожидает `str` или UTF-8 bytes и парсит через `json.loads(...)`.
   - Аудио в JSON всегда base64 string.
   - Бинарные websocket frames для аудио не использовать в MVP.

6. **Не угадывать WebSocket endpoint.**
   - В SDK добавить настройку `realtime_url`.
   - Если `url` не передан в `connect()` и `GIGACHAT_REALTIME_URL` не задан, выбрасывать понятный `ValueError`.
   - Не derive-ить endpoint из `base_url`, пока нет подтверждённого backend path.

7. **Не ломать импорт `gigachat` без realtime extras.**
   - `websockets`, `sounddevice`, `numpy` должны импортироваться lazy.
   - `import gigachat` должен работать без `pip install "gigachat[realtime]"`.
   - Ошибка отсутствующей зависимости должна возникать только при вызове realtime/audio helper API.

8. **Python 3.8+ обязателен.**
   - Не использовать `X | Y`.
   - Использовать `Optional`, `Union`, `List`, `Dict`, `Tuple`.
   - Для `TypedDict`, `Literal`, `NotRequired`, `Required` использовать `typing_extensions`.
   - Учитывать `mypy strict` и `ruff target-version = py38`.

9. **OpenAI SDK — ориентир по UX, не копипаста.**
   - Можно повторять паттерны: connection manager, async iterator, `.send`, `.recv`, `.parse_event`, `.send_raw`, event handlers.
   - Нельзя копировать код wholesale.
   - Надо адаптировать под GigaVoice sequence: первым событием после открытия соединения идут `settings`, затем `input.audio_content` / `input.synthesis_content` / `function_result`.

---

## 2. Non-goals

Не реализовывать в рамках этого плана:

- gRPC;
- protobuf;
- WebRTC;
- автоматический reconnect с восстановлением GigaVoice-контекста;
- автоматическое выполнение functions;
- real VAD на клиенте;
- SSML chunker;
- автоматическое создание `settings.context` при reconnect;
- hardcoded endpoint;
- изменение chat/completions REST API;
- root-level deprecated shim вида `client.voice(...)`.

---

## 3. Dependencies и extras

В `pyproject.toml` добавить optional dependencies.

Рекомендуемая схема:

```toml
[project.optional-dependencies]
realtime = [
    "websockets>=13,<16",
]
voice_helpers = [
    "sounddevice>=0.5.1",
    "numpy>=1.24,<2; python_version == '3.8'",
    "numpy>=2.0.2; python_version >= '3.9'",
]
realtime_voice = [
    "websockets>=13,<16",
    "sounddevice>=0.5.1",
    "numpy>=1.24,<2; python_version == '3.8'",
    "numpy>=2.0.2; python_version >= '3.9'",
]
```

Почему так:

- `realtime` нужен для transport-only пользователей;
- `voice_helpers` нужен для пользователей, которым нужны microphone/speaker helpers;
- `realtime_voice` удобен для demo/example установки одной extra-группой;
- `numpy>=2` нельзя навязывать Python 3.8, потому что библиотека поддерживает Python 3.8.

Все imports делать lazy:

```python
def _require_websockets() -> Any:
    try:
        from websockets.asyncio.client import connect
    except ImportError as exc:
        raise ImportError('Install `gigachat[realtime]` to use realtime WebSocket API') from exc
    return connect
```

Для `sounddevice` / `numpy` аналогично:

```python
def _require_voice_helpers() -> Tuple[Any, Any]:
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as exc:
        raise ImportError('Install `gigachat[voice_helpers]` or `gigachat[realtime_voice]` to use audio helpers') from exc
    return np, sd
```

---

## 4. Предлагаемая структура файлов

Добавлять файлы маленькими slices. Не создавать всё сразу.

```text
src/gigachat/types/realtime.py
src/gigachat/models/realtime.py
src/gigachat/api/realtime.py
src/gigachat/resources/realtime.py
src/gigachat/realtime/__init__.py
src/gigachat/realtime/_base64.py
src/gigachat/realtime/_events.py
src/gigachat/realtime/audio.py
src/gigachat/settings.py                       # добавить realtime_url
src/gigachat/client.py                         # добавить realtime/a_realtime resources
src/gigachat/resources/__init__.py
src/gigachat/models/__init__.py
src/gigachat/types/__init__.py                 # если пакета types ещё нет
examples/example_realtime_text.py
examples/example_realtime_microphone.py
docs/internal/RESOURCE_REALTIME_PROGRESS.md
```

Тесты:

```text
tests/unit/gigachat/realtime/test_event_params.py
tests/unit/gigachat/realtime/test_event_models.py
tests/unit/gigachat/realtime/test_base64_audio.py
tests/unit/gigachat/realtime/test_async_connection.py
tests/unit/gigachat/realtime/test_sync_connection.py
tests/unit/gigachat/realtime/test_resources.py
tests/unit/gigachat/realtime/test_audio_helpers.py
```

---

## 5. API shape: как должно выглядеть у пользователя

### 5.1. Async text-only / no microphone

```python
import asyncio
from uuid import uuid4

from gigachat import GigaChat

async def main() -> None:
    settings = {
        "voice_call_id": str(uuid4()),
        "mode": "RECOGNIZE_GIGACHAT_SYNTHESIS",
        "output_modalities": "TEXT",
        "enable_transcribe_input": True,
        "audio": {"input": {"audio_encoding": "PCM_S16LE", "sample_rate": 16000}},
    }

    async with GigaChat(credentials="...") as client:
        async with client.a_realtime.connect(settings=settings, url="wss://...") as connection:
            await connection.input_audio.send(b"...pcm16 bytes...", speech_start=True, speech_end=True)

            async for event in connection:
                if event.type == "output_transcription":
                    print(event.text)
                elif event.type == "output.additional_data":
                    break
                elif event.type == "error":
                    print(event.message)
                    break

asyncio.run(main())
```

### 5.2. Async with microphone/speaker helpers

```python
from uuid import uuid4

from gigachat import GigaChat
from gigachat.realtime.audio import RealtimeMicrophone, RealtimeSpeaker

settings = {
    "voice_call_id": str(uuid4()),
    "mode": "RECOGNIZE_GIGACHAT_SYNTHESIS",
    "output_modalities": "AUDIO_TEXT",
    "enable_transcribe_input": True,
    "audio": {
        "input": {"audio_encoding": "PCM_S16LE", "sample_rate": 16000},
        "output": {"audio_encoding": "PCM_S16LE"},
    },
}

async with GigaChat(credentials="...") as client:
    async with client.a_realtime.connect(settings=settings, url="wss://...") as connection:
        async with RealtimeMicrophone(sample_rate=16000, channels=1, chunk_ms=100) as mic:
            async with RealtimeSpeaker(sample_rate=16000, channels=1) as speaker:
                async for chunk in mic:
                    await connection.input_audio.send(chunk)

                    # In real apps receiving and sending should run in separate tasks.
                    event = await connection.recv()
                    if event.type == "output.audio":
                        await speaker.write(event.audio_chunk)
```

### 5.3. Callback/event-handler style

```python
manager = client.a_realtime.connect(settings=settings, url="wss://...")

@manager.on("output_transcription")
async def on_text(event):
    print(event.text)

@manager.on("error")
async def on_error(event):
    print(event.status, event.message)

async with manager as connection:
    await connection.input_audio.send(chunk, speech_start=True)
    await connection.dispatch_events()
```

### 5.4. Sync style

```python
with GigaChat(credentials="...") as client:
    with client.realtime.connect(settings=settings, url="wss://...") as connection:
        connection.input_audio.send(chunk, speech_start=True, speech_end=True)

        for event in connection:
            if event.type == "output_transcription":
                print(event.text)
            elif event.type == "output.additional_data":
                break
```

---

## 6. JSON event protocol для SDK

### 6.1. Общие правила

Все outbound client events имеют поле `type`.

Все inbound server events должны парситься в модель с полем `type`.

Если backend JSON event не содержит `type`, парсер может попытаться распознать legacy oneof-style object:

```json
{"output": {"audio": {"audio_chunk": "..."}}}
```

и нормализовать в:

```json
{"type": "output.audio", "audio_chunk": "..."}
```

Но основной контракт SDK — type-driven JSON:

```json
{"type": "input.audio_content", "audio_chunk": "base64...", "speech_start": true}
```

### 6.2. Аудио

В Python public API audio chunk — `bytes`.

В JSON wire payload audio chunk — base64 `str`.

SDK обязан кодировать перед отправкой:

```python
base64.b64encode(audio_chunk).decode("ascii")
```

SDK обязан декодировать серверный audio:

```python
base64.b64decode(audio_chunk)
```

Server event model `OutputAudioEvent.audio_chunk` должен отдавать пользователю `bytes`, не base64 string.

### 6.3. Размеры и ограничения

Перед отправкой JSON frame проверять размер UTF-8 bytes:

```python
len(json_payload.encode("utf-8")) <= 4 * 1024 * 1024
```

Если больше — выбрасывать `ValueError` до отправки.

Для PCM_S16LE можно soft-check длительности чанка:

```python
seconds = len(audio_chunk) / (sample_rate * channels * 2)
```

Если `seconds > 2`, выбросить `ValueError` или warning по параметру `validate_audio_chunks=True`. В MVP лучше `ValueError`, чтобы не нарушать backend-limit.

---

## 7. Data model cheat-sheet

Codex должен понимать, зачем нужна каждая модель. Не добавляй модель “просто потому что поле есть в документе”. Каждая модель должна решать одну задачу: typed input params, parsed server event, helper serialization или audio helper state.

### 7.1. Request params: `src/gigachat/types/realtime.py`

Request params — это `TypedDict`, а не Pydantic. Причина: как в OpenAI SDK, пользователь часто передаёт обычные dict-ы, а IDE получает autocomplete/type-checking.

Использовать `typing_extensions`:

```python
from typing_extensions import Literal, NotRequired, Required, TypedDict
```

#### `RealtimeMode`

Type alias:

```python
RealtimeMode = Literal[
    "RECOGNIZE_GIGACHAT_SYNTHESIS",
    "RECOGNIZE_SYNTHESIS",
    "GIGACHAT_SYNTHESIS",
]
```

Зачем: ограничить backend mode строками из документа.

Не добавлять `RESOURCE_REALTIME`: это namespace SDK, не backend mode.

#### `RealtimeOutputModalities`

```python
RealtimeOutputModalities = Literal["AUDIO", "AUDIO_TEXT", "TEXT"]
```

Зачем: управляет тем, ждём ли audio events, text events или оба.

#### `RealtimeAudioEncoding`

```python
RealtimeAudioEncoding = Literal["PCM_S16LE", "OPUS", "PCM_ALAW"]
```

Зачем: settings.audio.input/output и validation helpers.

#### `RealtimeFirstSpeakerParam`

Поля:

- `type`: `"model" | "user"`;
- `lock_first_in`: optional bool.

Зачем: старт разговора от модели. Если `type="model"`, в `settings.context.messages` должен быть валидный стартовый контекст.

SDK не обязан валидировать весь бизнес-контекст, но может проверить очевидное: не пустой context для `model`.

#### `RealtimeDisableInterruptionFunctionParam`

Поля:

- `name`: required str;
- `on_execution`: optional bool;
- `after_result`: optional bool.

Зачем: отключение перебиваний вокруг функций.

#### `RealtimeDisableInterruptionParam`

Поля:

- `functions`: optional list of `RealtimeDisableInterruptionFunctionParam`.

Зачем: группирует настройки блокировки перебивания.

#### `RealtimeFunctionRankerParam`

Поля:

- `enable`: optional bool;
- `top_n`: optional int.

Зачем: настройки ранжирования функций. Использовать поле `enable`, как в Word-документе JSON schema. Не использовать proto-name `enabled`.

#### `RealtimeFunctionRegistryParam`

Поля:

- `profile`: optional str;
- `labels`: optional list[str];
- `ab_flags`: optional str, содержащий JSON.

Зачем: запрос функций из function registry.

SDK не парсит `ab_flags`, только передаёт строку.

#### `RealtimeFunctionParam`

Минимально:

- `name`: str;
- `description`: optional str;
- `parameters`: optional dict[str, Any].

Зачем: клиентские функции по аналогии с chat/completions.

Разрешить `extra` через `Mapping[str, Any]` невозможно в TypedDict, поэтому для полной гибкости можно типизировать как `Dict[str, Any]` в местах, где текущие chat models уже используют произвольное описание функции. Не блокировать unknown function fields.

#### `RealtimeGigaChatSettingsParam`

Поля:

- `model`: optional str;
- `preset`: optional str;
- `temperature`: optional float;
- `top_p`: optional float;
- `repetition_penalty`: optional float;
- `profanity_check`: optional bool;
- `filters_settings`: optional dict[str, Any];
- `function_ranker`: optional `RealtimeFunctionRankerParam`;
- `functions`: optional list of function descriptions;
- `current_time`: optional int;
- `function_registry`: optional `RealtimeFunctionRegistryParam`;
- `filter_stub_phrases`: optional list[str].

Зачем: настройки генерации GigaChat внутри GigaVoice.

Не валидировать модельные hyperparams сверх типа. Backend отдаст ошибку, если значение недопустимо.

#### `RealtimeAudioChunkMetaParam`

Поля:

- `force_co_speech`: optional bool.

Зачем: документ описывает признак для гарантированного игнорирования чанка. Использовать doc-name `force_co_speech`, не proto-name.

#### `RealtimeInputAudioSettingsParam`

Поля:

- `model`: optional str;
- `audio_encoding`: optional `RealtimeAudioEncoding`;
- `sample_rate`: optional int;
- `silence_phrases`: optional list[str];
- `silence_phrases_timeout`: optional duration;
- `silence_timeout`: optional duration;
- `stop_phrases`: optional list[str];
- `ignore_phrases`: optional list[str].

Duration representation for JSON: use string or float? В плане зафиксировать как:

- public SDK принимает `float` seconds или ISO-ish string? Для MVP не усложнять: `Union[float, str]`.
- JSON отправляет как передано.

Почему: backend JSON schema ещё не подтверждена, нельзя навязать формат duration.

#### `RealtimeTriggerFunctionParam`

Поля:

- `enable`: required bool if object is present;
- `mode`: optional `"WHITELIST" | "BLACKLIST"`;
- `function_names`: optional list[str].

Зачем: звуки ожидания при долгих функциях.

#### `RealtimeTriggerGenerationParam`

Поля:

- `enable`: required bool if object is present;
- `timeout`: required `Union[float, str]`.

Зачем: звуки ожидания при долгой генерации.

#### `RealtimeStubSoundsParam`

Поля:

- `trigger_function`: optional `RealtimeTriggerFunctionParam`;
- `trigger_generation`: optional `RealtimeTriggerGenerationParam`;
- `sounds`: required/optional list[str].

Зачем: настройки предзаписанных TTS.DL звуков.

Не использовать proto-name `trigger_delay`; protobuf запрещён.

#### `RealtimeOutputAudioSettingsParam`

Поля:

- `voice`: optional str;
- `audio_encoding`: optional `RealtimeAudioEncoding`;
- `stub_sounds`: optional `RealtimeStubSoundsParam`.

Зачем: настройки синтеза.

#### `RealtimeAudioSettingsParam`

Поля:

- `input`: optional `RealtimeInputAudioSettingsParam`;
- `output`: optional `RealtimeOutputAudioSettingsParam`.

Зачем: единый блок audio settings.

#### `RealtimeContextFunctionCallParam`

Поля:

- `name`: str;
- `arguments`: str or dict?

Для MVP использовать `Dict[str, Any]` or `str`? Документ говорит JSON string для function call arguments. Чтобы не ломать текущие function structures, разрешить `Union[str, Dict[str, Any]]`.

#### `RealtimeContextMessageParam`

Поля:

- `role`: required str;
- `content`: required str;
- `inline_data`: optional dict[str, str];
- `attachments`: optional list[str];
- `function_call`: optional `RealtimeContextFunctionCallParam`;
- `function_name`: optional str;
- `functions_state_id`: optional str;
- `functions`: optional list[dict[str, Any]].

Зачем: стартовый контекст и reconnect continuation.

SDK не должен сам чистить context в MVP, но docs должны объяснить правила.

#### `RealtimeContextParam`

Поля:

- `messages`: required list[`RealtimeContextMessageParam`].

Зачем: wrapper для `settings.context`.

#### `RealtimeSettingsParam`

Поля:

- `voice_call_id`: required str;
- `mode`: optional `RealtimeMode`;
- `output_modalities`: optional `RealtimeOutputModalities`;
- `first_speaker`: optional `RealtimeFirstSpeakerParam`;
- `disable_interruption`: optional `RealtimeDisableInterruptionParam`;
- `gigachat`: optional `RealtimeGigaChatSettingsParam`;
- `audio`: optional `RealtimeAudioSettingsParam`;
- `context`: optional `RealtimeContextParam`;
- `disable_vad`: optional bool;
- `enable_transcribe_input`: optional bool;
- `enable_denoiser`: optional bool;
- `enable_prefetch`: optional bool;
- `enable_person_identity`: optional bool;
- `enable_whisper`: optional bool;
- `enable_emotion`: optional bool;
- `enable_transcribe_silence_phrases`: optional bool;
- `flags`: optional list[str].

Зачем: первое событие на WebSocket connection. `voice_call_id` обязателен.

SDK validation:

- `voice_call_id` required;
- если `enable_prefetch/person_identity/whisper/emotion=True`, желательно warning/ValueError если `enable_transcribe_input` не true;
- если `mode="GIGACHAT_SYNTHESIS"` и `enable_whisper=True`, backend может вернуть error; SDK может не валидировать бизнес-правило.

### 7.2. Client event params

#### `RealtimeSettingsEventParam`

```python
{
    "type": "settings",
    "settings": RealtimeSettingsParam,
}
```

Зачем: первое событие connection.

#### `RealtimeInputAudioContentEventParam`

Public Python input:

```python
{
    "type": "input.audio_content",
    "audio_chunk": bytes,
    "speech_start": bool,
    "speech_end": bool,
    "meta": {"force_co_speech": bool},
}
```

Wire JSON:

```json
{
  "type": "input.audio_content",
  "audio_chunk": "base64...",
  "speech_start": true,
  "speech_end": false,
  "meta": {"force_co_speech": false}
}
```

Зачем: отправить audio chunk на ASR/VAD.

#### `RealtimeInputSynthesisContentEventParam`

```python
{
    "type": "input.synthesis_content",
    "text": str,
    "content_type": "text" | "ssml",
    "is_final": bool,
}
```

Зачем: режим `RECOGNIZE_SYNTHESIS`, когда бизнес-логика/GigaChat на стороне пользователя, а GigaVoice только распознаёт и синтезирует.

#### `RealtimeFunctionResultEventParam`

```python
{
    "type": "function_result",
    "content": str | dict[str, Any],
    "function_name": str,
}
```

Зачем: ответ на server event `function_call`.

Serialization rule:

- если `content` dict/list — `json.dumps(..., ensure_ascii=False)`;
- если `content` str — передать как есть, но не валидировать JSON в SDK;
- backend ожидает valid JSON string, поэтому helper docs должны рекомендовать dict.

#### `RealtimeClientEventParam`

Union of all client events.

Зачем: `connection.send(event)` принимает один тип.

### 7.3. Server event models: `src/gigachat/models/realtime.py`

Server events — Pydantic BaseModel. Причина: SDK парсит JSON, пользователь получает typed objects с helpers `.model_dump()` / `.model_dump_json()`.

Общее правило:

```python
from pydantic import BaseModel, ConfigDict

class RealtimeServerEvent(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str
```

`extra="allow"` важно: backend может прислать новые поля, и SDK не должен их терять.

#### `OutputAudioEvent`

Fields:

- `type: Literal["output.audio"]`;
- `audio_chunk: bytes`;
- `audio_duration: Optional[Union[float, str]]`;
- `is_final: Optional[bool]`.

Зачем: audio response. SDK декодирует base64 в bytes.

#### `OutputAdditionalDataEvent`

Fields:

- `type: Literal["output.additional_data"]`;
- `prompt_tokens`: optional int;
- `completion_tokens`: optional int;
- `total_tokens`: optional int;
- `precached_prompt_tokens`: optional int;
- `gigachat_model_info`: optional `GigaChatModelInfo`;
- `finish_reason`: optional str.

Зачем: финальная metadata / usage / finish reason.

#### `GigaChatModelInfo`

Fields:

- `name`: optional str;
- `version`: optional str.

Зачем: nested object in additional data.

#### `OutputInterruptedEvent`

Fields:

- `type: Literal["output.interrupted"]`;
- `interrupted: bool = True`.

Зачем: пользователь должен остановить проигрывание audio/text для текущей генерации.

#### `FunctionCallEvent`

Fields:

- `type: Literal["function_call"]`;
- `name`: str;
- `arguments`: str;
- `timestamp`: optional int.

Зачем: backend просит клиента выполнить функцию.

SDK не выполняет функцию сам.

#### `InputTranscriptionEvent`

Fields:

- `type: Literal["input_transcription"]`;
- `text`: str;
- `unnormalized_text`: optional str;
- `prefetch`: optional bool;
- `person_identity`: optional `PersonIdentity`;
- `whisper`: optional bool;
- `emotion`: optional `Emotion`;
- `timestamp`: optional int.

Зачем: транскрипция пользовательской речи.

#### `PersonIdentity`

Fields:

- `age`: optional str;
- `gender`: optional str;
- `age_score`: optional float;
- `gender_score`: optional float.

Зачем: ASR detection fields.

#### `Emotion`

Fields:

- `positive`: optional float;
- `neutral`: optional float;
- `negative`: optional float.

Зачем: ASR emotion detection.

#### `OutputTranscriptionEvent`

Fields:

- `type: Literal["output_transcription"]`;
- `text`: optional str;
- `stub_text`: optional str;
- `silence_phrase`: optional bool;
- `inline_data`: optional dict[str, str];
- `functions_state_id`: optional str;
- `finish_reason`: optional str;
- `timestamp`: optional int.

Зачем: текст реплики модели, включая фильтр-заглушки и silence phrases.

#### `InputFilesEvent`

Fields:

- `type: Literal["input_files"]`;
- `files`: list[`InputFileInfo`].

Зачем: режим `GIGACHAT_SYNTHESIS`, где GigaVoice возвращает IDs загруженных audio files для продолжения контекста.

#### `InputFileInfo`

Fields:

- `id`: str;
- `type`: str.

Зачем: file metadata.

#### `PlatformFunctionProcessingEvent`

Fields:

- `type: Literal["platform_function_processing"]`;
- `name`: str;
- `timestamp`: optional int.

Зачем: визуальная индикация выполнения платформенной функции.

#### `RealtimeErrorEvent`

Fields:

- `type: Literal["error"]`;
- `status`: optional int;
- `status_code`: optional int;
- `message`: str.

Зачем: blocking error. По документу GigaVoice после `error` закрывает взаимодействие. SDK должен вернуть событие пользователю; connection close произойдёт потом.

Compatibility:

- добавить property `.code`? Не обязательно.
- добавить property `.status_value`, который возвращает `status` или `status_code`, можно в отдельном slice.

#### `RealtimeWarningEvent`

Fields:

- `type: Literal["warning"]`;
- `message`: str.

Зачем: non-blocking warning.

#### `RealtimeUnknownEvent`

Fields:

- `type`: str;
- любые extra fields.

Зачем: forward compatibility.

#### `RealtimeServerEvent` union

Type alias for all server events.

Implementation detail:

- Pydantic discriminated union может быть сложным для Python 3.8/mypy.
- MVP можно сделать factory `parse_realtime_event(data: Mapping[str, Any]) -> RealtimeServerEvent` and return concrete classes.

### 7.4. Connection helper resources

По OpenAI-style connection должен иметь вложенные helper resources.

#### `RealtimeInputAudioResource`

Methods:

```python
async def send(self, audio_chunk: bytes, *, speech_start: Optional[bool] = None, speech_end: Optional[bool] = None, meta: Optional[RealtimeAudioChunkMetaParam] = None) -> None
```

Sync equivalent.

Зачем: удобнее, чем руками собирать event dict.

#### `RealtimeSynthesisResource`

Methods:

```python
async def send(self, text: str, *, content_type: Literal["text", "ssml"] = "text", is_final: bool = False) -> None
```

Зачем: `RECOGNIZE_SYNTHESIS` mode.

#### `RealtimeFunctionResultResource`

Methods:

```python
async def create(self, content: Union[str, Mapping[str, Any]], *, function_name: Optional[str] = None) -> None
```

Зачем: ответ на function_call.

#### `RealtimeSessionResource`

Не делать full dynamic `session.update` как у OpenAI, потому что GigaVoice sequence требует settings первым сообщением. Но можно добавить:

```python
async def send_settings(self, settings: RealtimeSettingsParam) -> None
```

и использовать это внутри connection manager.

В MVP публичный путь: `connect(settings=...)` сам отправляет settings.

### 7.5. Audio helper models: `src/gigachat/realtime/audio.py`

Эти helpers требуют `sounddevice` + `numpy`.

#### `RealtimeMicrophone`

Purpose: async iterator over PCM_S16LE audio chunks from input device.

Constructor:

```python
RealtimeMicrophone(
    sample_rate: int = 16000,
    channels: int = 1,
    chunk_ms: int = 100,
    dtype: str = "int16",
    device: Optional[Union[int, str]] = None,
)
```

Methods:

- async context manager;
- `__aiter__` yields `bytes`;
- `.close()`.

Implementation:

- use `sounddevice.InputStream`;
- callback receives numpy array;
- ensure mono default;
- convert to little-endian int16 contiguous bytes;
- push chunks into `asyncio.Queue` via `loop.call_soon_threadsafe`.

Why: examples can capture microphone without user writing PortAudio boilerplate.

#### `RealtimeSpeaker`

Purpose: play PCM_S16LE output chunks.

Constructor:

```python
RealtimeSpeaker(
    sample_rate: int = 16000,
    channels: int = 1,
    dtype: str = "int16",
    device: Optional[Union[int, str]] = None,
)
```

Methods:

- async context manager;
- `async write(audio_chunk: bytes) -> None`;
- `stop() -> None`;
- `.close()`.

Implementation:

- use `sounddevice.OutputStream`;
- keep internal queue or call `sd.play`? Prefer OutputStream with queue for streaming;
- convert bytes to numpy `int16` frames;
- interruption calls `.stop()` and drains queue.

Why: `output.interrupted` requires user to stop playback fast.

#### Base64/conversion helpers

In `src/gigachat/realtime/_base64.py`:

```python
def encode_audio(audio_chunk: bytes) -> str: ...
def decode_audio(audio_chunk: str) -> bytes: ...
def pcm16_duration_seconds(audio_chunk: bytes, sample_rate: int, channels: int = 1) -> float: ...
def validate_pcm16_chunk_duration(audio_chunk: bytes, sample_rate: int, channels: int = 1, max_seconds: float = 2.0) -> None: ...
```

In `audio.py`:

```python
def numpy_to_pcm16_bytes(array: Any) -> bytes: ...
def pcm16_bytes_to_numpy(audio_chunk: bytes) -> Any: ...
```

Why: tests can cover audio encoding without loading sounddevice.

---

## 8. Transport design

### 8.1. Async connection manager

`client.a_realtime.connect(...)` should return `AsyncRealtimeConnectionManager`, not immediately open socket.

Signature:

```python
def connect(
    self,
    *,
    settings: RealtimeSettingsParam,
    url: Optional[str] = None,
    extra_headers: Optional[Mapping[str, str]] = None,
    websocket_connection_options: Optional[Mapping[str, Any]] = None,
    max_frame_size: int = 4 * 1024 * 1024,
    validate_audio_chunks: bool = True,
) -> AsyncRealtimeConnectionManager: ...
```

Why:

- mirrors OpenAI SDK;
- lets user register handlers before opening connection;
- manager can queue initial settings event and send it after connect.

### 8.2. Opening WebSocket

Steps:

1. Resolve URL:
   - `url` argument;
   - `client.settings.realtime_url` / env `GIGACHAT_REALTIME_URL`;
   - otherwise raise `ValueError`.

2. Refresh/access token through existing auth path before WS handshake.

3. Build headers:
   - `Authorization: Bearer ...`;
   - `User-Agent`;
   - existing context headers if SDK already has helper for REST;
   - `extra_headers` override/merge.

4. Open websocket with `websockets.asyncio.client.connect`.

5. Create `AsyncRealtimeConnection`.

6. Immediately send settings event:

```json
{"type":"settings","settings":{...}}
```

7. Flush any queued messages registered before entering context.

### 8.3. AsyncRealtimeConnection methods

Required:

```python
async def recv(self) -> RealtimeServerEvent: ...
async def recv_bytes(self) -> bytes: ...
async def send(self, event: RealtimeClientEventParam) -> None: ...
async def send_raw(self, data: Union[str, bytes]) -> None: ...
def parse_event(self, data: Union[str, bytes]) -> RealtimeServerEvent: ...
async def close(self, *, code: int = 1000, reason: str = "") -> None: ...
def __aiter__(self) -> AsyncIterator[RealtimeServerEvent]: ...
```

Also attach helper resources:

```python
self.session = AsyncRealtimeSessionResource(self)
self.input_audio = AsyncRealtimeInputAudioResource(self)
self.synthesis = AsyncRealtimeSynthesisResource(self)
self.function_result = AsyncRealtimeFunctionResultResource(self)
```

### 8.4. Event handlers

Mirror OpenAI-style:

```python
def on(self, event_type: str, handler: Optional[Callable[..., Any]] = None): ...
def off(self, event_type: str, handler: Callable[..., Any]): ...
def once(self, event_type: str, handler: Optional[Callable[..., Any]] = None): ...
async def dispatch_events(self) -> None: ...
```

Behavior:

- specific handlers receive event with exact `event.type`;
- generic handlers registered under `"event"` receive all events;
- if `event.type == "error"` and no `error` or `event` handler is registered, `dispatch_events()` may raise `GigaChatException` after parsing the event;
- `recv()` and `async for` should not raise just because event type is `error`.

Why: matches OpenAI SDK ergonomics while preserving GigaVoice blocking-error semantics.

### 8.5. Sync implementation

Use `websockets.sync.client.connect` lazily.

Implement sync classes after async is stable:

- `RealtimeConnectionManager`;
- `RealtimeConnection`;
- sync helper resources.

No thread/event-loop hack in sync transport.

---

## 9. Serialization and parsing

### 9.1. `serialize_client_event(event)`

Input:

- TypedDict-like mapping;
- optional Pydantic BaseModel if future code adds models.

Output:

- JSON string.

Rules:

- do not include unset `None` values unless field explicitly needs null;
- encode audio bytes to base64 string;
- convert dict `function_result.content` to JSON string;
- validate final UTF-8 frame size;
- validate audio chunk duration if possible.

### 9.2. `parse_realtime_event(data)`

Input:

- `str` or `bytes` from WS;
- if bytes, decode UTF-8.

Steps:

1. `json.loads`.
2. Normalize legacy oneof-style to type-style if needed.
3. Dispatch by `type`.
4. For `output.audio`, decode base64 into bytes.
5. Return concrete Pydantic model.
6. Unknown type returns `RealtimeUnknownEvent`.

### 9.3. Legacy oneof-style normalization

Implement only if simple:

```python
{"output": {"audio": {...}}}               -> type "output.audio"
{"output": {"additional_data": {...}}}     -> type "output.additional_data"
{"output": {"interrupted": true}}          -> type "output.interrupted"
{"function_call": {...}}                    -> type "function_call"
{"input_transcription": {...}}              -> type "input_transcription"
{"output_transcription": {...}}             -> type "output_transcription"
{"input_files": {...}}                      -> type "input_files"
{"platform_function_processing": {...}}     -> type "platform_function_processing"
{"error": {...}}                            -> type "error"
{"warning": {...}}                          -> type "warning"
```

Why: backend JSON gateway might mirror old oneof/protobuf names instead of OpenAI-like event names.

---

## 10. Settings changes

Add to settings:

```python
realtime_url: Optional[str] = None
```

Env var:

```text
GIGACHAT_REALTIME_URL
```

Do not add `realtime_grpc_url`.

Do not derive from REST `base_url`.

---

## 11. Progress protocol

Create/update `docs/internal/RESOURCE_REALTIME_PROGRESS.md`.

Required format:

```md
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
| 01-docs-progress-reset | done | <hash> | Reset plan from protobuf to JSON. |
| 02-dependency-extras | pending |  |  |

## Log

### 2026-04-27 — slice 01-docs-progress-reset

Done:
- ...

Tests:
- not run, docs-only

Next:
- 02-dependency-extras

Risks:
- backend JSON endpoint must be confirmed
```

Every slice must append a new log entry.

Every slice must update the status table.

If tests are not run, write exactly why.

---

## 12. Commit-срезы

Codex must do exactly one slice per pass.

### 01-docs-progress-reset

Goal: replace old protobuf plan with this JSON plan and create/reset progress file.

Files:

- `docs/internal/RESOURCE_REALTIME_PLAN.md`
- `docs/internal/RESOURCE_REALTIME_PROGRESS.md`

Commit:

```text
docs(realtime): reset plan to json websocket implementation
```

Progress notes:

- State that protobuf/gRPC are now forbidden.
- State that JSON endpoint/gateway must exist.

Tests:

- Not required, docs-only.

Stop after commit.

---

### 02-dependency-extras

Goal: add optional dependencies only.

Files:

- `pyproject.toml`

Add:

- `realtime = ["websockets>=13,<16"]`
- `voice_helpers = ["sounddevice>=0.5.1", numpy markers]`
- `realtime_voice = [...]`

Do not import these deps anywhere yet.

Commit:

```text
chore(realtime): add optional websocket and voice helper extras
```

Tests:

- `python -c "import gigachat"`
- existing unit import smoke if available.

Stop after commit.

---

### 03-realtime-settings-config

Goal: add `realtime_url` config and env support.

Files:

- `src/gigachat/settings.py`
- tests for env/config if settings tests exist

Rules:

- Add only `realtime_url`.
- Do not add gRPC URL.
- Do not open websockets.

Commit:

```text
feat(realtime): add realtime websocket url setting
```

Tests:

- settings unit tests.

Stop after commit.

---

### 04-client-param-types

Goal: add TypedDict request params and literal aliases.

Files:

- `src/gigachat/types/__init__.py` if needed
- `src/gigachat/types/realtime.py`
- `tests/unit/gigachat/realtime/test_event_params.py`

Implement only types, no runtime transport.

Commit:

```text
feat(realtime): add json client event param types
```

Tests:

- import/type smoke tests.

Stop after commit.

---

### 05-server-event-models

Goal: add Pydantic server event models and parser factory.

Files:

- `src/gigachat/models/realtime.py`
- `src/gigachat/models/__init__.py`
- `tests/unit/gigachat/realtime/test_event_models.py`

Implement:

- concrete event classes;
- `parse_realtime_event`;
- unknown event fallback;
- `output.audio` base64 decode into bytes;
- legacy oneof normalization if small.

Do not add WebSocket transport.

Commit:

```text
feat(realtime): add json server event models
```

Tests:

- parser tests for each server event type.

Stop after commit.

---

### 06-client-event-serialization

Goal: serialize client events to JSON frames.

Files:

- `src/gigachat/realtime/__init__.py`
- `src/gigachat/realtime/_base64.py`
- `src/gigachat/realtime/_events.py`
- `tests/unit/gigachat/realtime/test_base64_audio.py`
- `tests/unit/gigachat/realtime/test_event_params.py`

Implement:

- `encode_audio` / `decode_audio`;
- frame size validation;
- PCM duration validation;
- `serialize_client_event`;
- dict `function_result.content` -> JSON string.

Do not add WebSocket transport.

Commit:

```text
feat(realtime): add json client event serialization
```

Tests:

- serialize settings;
- serialize audio and base64;
- oversize frame error;
- PCM chunk >2 sec error;
- function result content conversion.

Stop after commit.

---

### 07-async-websocket-connection

Goal: add async low-level WebSocket connection and manager.

Files:

- `src/gigachat/api/realtime.py`
- `tests/unit/gigachat/realtime/test_async_connection.py`

Implement:

- lazy `websockets` import;
- `AsyncRealtimeConnectionManager`;
- `AsyncRealtimeConnection`;
- `recv`, `recv_bytes`, `send`, `send_raw`, `parse_event`, `close`, `__aiter__`;
- initial settings sent immediately after connect;
- auth headers using existing SDK auth/header helpers.

Do not add client resource property yet.

Commit:

```text
feat(realtime): add async json websocket connection
```

Tests:

- fake/mock websocket connect;
- initial settings first frame;
- send audio frame;
- recv parses event;
- close closes websocket;
- missing `websockets` raises install-extra hint.

Stop after commit.

---

### 08-event-handler-registry

Goal: add `.on`, `.off`, `.once`, `.dispatch_events()` to async connection and manager.

Files:

- `src/gigachat/realtime/_events.py` or `src/gigachat/api/realtime.py`
- `tests/unit/gigachat/realtime/test_async_connection.py`

Can implement small internal registry.

Rules:

- specific event handlers by exact `event.type`;
- generic `event` handler;
- once handler removed after first call;
- manager-level handlers transfer into connection on enter.

Commit:

```text
feat(realtime): add websocket event handlers
```

Tests:

- handler called;
- once called once;
- off removes;
- manager handlers transfer.

Stop after commit.

---

### 09-async-helper-resources

Goal: add OpenAI-style nested helper resources on async connection.

Files:

- `src/gigachat/api/realtime.py`
- tests

Implement:

- `connection.session.send_settings(...)`;
- `connection.input_audio.send(...)`;
- `connection.synthesis.send(...)`;
- `connection.function_result.create(...)`.

Rules:

- helpers call `connection.send(...)`;
- no business state machine;
- no automatic function execution.

Commit:

```text
feat(realtime): add async realtime helper resources
```

Tests:

- each helper emits expected JSON event.

Stop after commit.

---

### 10-async-resource-namespace

Goal: add `client.a_realtime.connect(...)` resource namespace.

Files:

- `src/gigachat/resources/realtime.py`
- `src/gigachat/resources/__init__.py`
- `src/gigachat/client.py`
- tests

Implement:

- `AsyncRealtimeResource.connect(...)` returns `AsyncRealtimeConnectionManager`;
- cached property `a_realtime` on client;
- no sync property yet.

Commit:

```text
feat(resources): add async realtime resource namespace
```

Tests:

- `client.a_realtime` exists;
- `connect` passes settings/url to manager;
- no deprecated warning.

Stop after commit.

---

### 11-sync-websocket-connection

Goal: add sync low-level connection and manager.

Files:

- `src/gigachat/api/realtime.py`
- `tests/unit/gigachat/realtime/test_sync_connection.py`

Implement sync equivalents:

- `RealtimeConnectionManager`;
- `RealtimeConnection`;
- `recv`, `recv_bytes`, `send`, `send_raw`, `parse_event`, `close`, `__iter__`;
- lazy `websockets.sync.client.connect`;
- initial settings first frame;
- handler methods sync-compatible.

Commit:

```text
feat(realtime): add sync json websocket connection
```

Tests:

- fake sync websocket;
- first settings frame;
- event parsing;
- close.

Stop after commit.

---

### 12-sync-helper-resources

Goal: add sync nested helper resources.

Files:

- `src/gigachat/api/realtime.py`
- tests

Implement sync:

- `connection.session.send_settings(...)`;
- `connection.input_audio.send(...)`;
- `connection.synthesis.send(...)`;
- `connection.function_result.create(...)`.

Commit:

```text
feat(realtime): add sync realtime helper resources
```

Tests:

- each helper emits expected JSON event.

Stop after commit.

---

### 13-sync-resource-namespace

Goal: add `client.realtime.connect(...)` resource namespace.

Files:

- `src/gigachat/resources/realtime.py`
- `src/gigachat/client.py`
- tests

Implement:

- `RealtimeResource.connect(...)` returns sync manager;
- cached property `realtime` on client.

Commit:

```text
feat(resources): add sync realtime resource namespace
```

Tests:

- `client.realtime` exists;
- `connect` passes settings/url.

Stop after commit.

---

### 14-voice-helper-conversions

Goal: add numpy conversion helpers without opening devices.

Files:

- `src/gigachat/realtime/audio.py`
- `tests/unit/gigachat/realtime/test_audio_helpers.py`

Implement:

- lazy numpy import;
- `numpy_to_pcm16_bytes`;
- `pcm16_bytes_to_numpy`;
- maybe `chunk_pcm16_bytes`.

Do not import/use sounddevice yet.

Commit:

```text
feat(realtime): add numpy pcm16 audio helpers
```

Tests:

- mock or real numpy if installed in dev;
- conversion roundtrip.

Stop after commit.

---

### 15-sounddevice-helpers

Goal: add microphone and speaker helpers.

Files:

- `src/gigachat/realtime/audio.py`
- tests

Implement:

- `RealtimeMicrophone` async iterator;
- `RealtimeSpeaker` async writer;
- lazy sounddevice import;
- no actual device usage in unit tests; mock sounddevice streams.

Commit:

```text
feat(realtime): add sounddevice microphone and speaker helpers
```

Tests:

- mocked stream start/stop;
- microphone callback pushes bytes;
- speaker write converts bytes and enqueues/writes;
- `stop()` drains pending playback.

Stop after commit.

---

### 16-examples-text-and-functions

Goal: add examples without audio device dependency.

Files:

- `examples/example_realtime_text.py`
- `examples/example_realtime_functions.py` optional
- `examples/README.md`

Commit:

```text
docs(realtime): add json websocket text examples
```

Examples must mention:

- requires backend JSON websocket endpoint;
- install `gigachat[realtime]`;
- set `GIGACHAT_REALTIME_URL`.

Stop after commit.

---

### 17-example-microphone

Goal: add push-to-talk / microphone example.

Files:

- `examples/example_realtime_microphone.py`
- `examples/README.md`

Commit:

```text
docs(realtime): add microphone realtime example
```

Example must mention:

- install `gigachat[realtime_voice]`;
- PortAudio/system dependency may be needed;
- audio defaults: PCM_S16LE, 16kHz, mono.

Stop after commit.

---

### 18-readme-docs

Goal: document public API in README or docs.

Files:

- `README.md`
- maybe `MIGRATION_GUIDE.md` only if branch already uses one

Commit:

```text
docs(realtime): document resource realtime api
```

Include:

- install extras;
- JSON endpoint requirement;
- API snippets;
- known limitations;
- error handling semantics.

Stop after commit.

---

### 19-integration-smoke-tests

Goal: add optional integration tests.

Files:

- `tests/integration/test_realtime_json_ws.py`

Env:

```text
GIGACHAT_REALTIME_URL
GIGACHAT_CREDENTIALS or existing auth env
```

Marker: existing `integration` marker.

Commit:

```text
test(realtime): add json websocket integration smoke tests
```

Tests:

- connect and send settings;
- optionally send tiny silence/audio chunk if endpoint supports;
- skip if env missing.

Stop after commit.

---

### 20-final-audit

Goal: final no-protobuf/no-gRPC audit.

Commands:

```bash
grep -R "grpc\|protobuf\|voice_pb2\|google.protobuf" -n src tests examples docs || true
```

Allowed matches:

- docs saying gRPC/protobuf are forbidden;
- this plan/progress.

Commit:

```text
chore(realtime): audit json websocket implementation
```

Progress notes:

- list tests run;
- list known remaining risk: backend JSON endpoint requirement.

Stop after commit.

---

## 13. Test strategy

### Unit tests

Must cover:

- import without extras;
- missing `websockets` message;
- missing `sounddevice`/`numpy` message;
- settings URL env support;
- JSON serialization of each client event;
- parser for each server event;
- unknown event fallback;
- legacy oneof normalization;
- audio base64 encode/decode;
- PCM duration validation;
- async connection manager sends settings first;
- sync connection manager sends settings first;
- event handlers;
- helper resources;
- audio helpers with mocked sounddevice.

### Integration tests

Integration tests must be skipped unless env is present.

Do not require microphone in integration tests.

### Type/lint

Run what repo already expects, likely:

```bash
pytest tests/unit/gigachat/realtime
mypy src/gigachat
ruff check src tests
```

If full mypy/ruff is too slow in Codex environment, run targeted tests and write exact limitation in progress.

---

## 14. Error handling semantics

- `recv()` returns `RealtimeErrorEvent` for `type="error"`.
- `async for event in connection` yields error event, then may end when server closes.
- `dispatch_events()` may raise only if error event has no handler.
- Connection-level network failures should raise existing SDK connection exceptions where possible.
- Server `warning` is never raised automatically.
- Server `output.interrupted` is not an error; it is a control event instructing playback stop.

---

## 15. Auth and headers

Reuse existing SDK behavior as much as possible.

Required headers:

- auth bearer token;
- user agent;
- context headers already supported by SDK, such as `X-Session-ID`, `X-Request-ID`, `X-Client-ID`, custom headers.

Do not set `X-Session-ID` from `voice_call_id` automatically unless existing SDK already does so. GigaVoice backend uses `voice_call_id` for tracing; user may also set session header explicitly.

If WS handshake gets auth failure and existing REST client supports token refresh, one retry is acceptable, but do not implement complex retry/reconnect in MVP.

---

## 16. Known protocol gaps to track

Because protobuf is removed and backend JSON schema is not confirmed, track these in progress:

1. Exact JSON endpoint path.
2. Whether backend expects event `type` envelope or oneof-style JSON.
3. Duration format: seconds number vs string vs structured object.
4. Error status field name: `status` vs `status_code`.
5. Whether input audio base64 field should be named `audio_chunk` or nested under `audio_content`.
6. Whether output audio base64 field should be `audio_chunk` or nested under `audio`.
7. Whether `platform_function_processing` is present in JSON events.
8. Whether `silence_phrase` is present in output transcription.

Do not block unit implementation on these; design parser/serializer to be easy to adapt.

---

## 17. Implementation style notes

- Keep modules small.
- Avoid circular imports between `client.py`, `resources/realtime.py`, and `api/realtime.py`.
- Put heavy optional imports inside functions/classes that actually need them.
- Prefer explicit functions over magic.
- Do not hide backend events; preserve unknown fields.
- Keep user API stable and simple.
- Add docstrings only where they clarify protocol semantics.

---

## 18. Final expected state

After all slices, a user can do:

```bash
pip install "gigachat[realtime]"
```

for JSON WebSocket text/audio transport, or:

```bash
pip install "gigachat[realtime_voice]"
```

for WebSocket plus microphone/speaker helpers.

The SDK exposes:

```python
client.a_realtime.connect(settings=..., url=...)
client.realtime.connect(settings=..., url=...)
```

The connection exposes:

```python
connection.send(...)
connection.recv()
connection.parse_event(...)
connection.input_audio.send(...)
connection.synthesis.send(...)
connection.function_result.create(...)
connection.on(...)
connection.dispatch_events()
```

There is no gRPC code, no protobuf code, no generated files, and no dependency on `voice.proto`.
