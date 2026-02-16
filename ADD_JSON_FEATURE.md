# Add `response_format` (JSON Schema) support to `gigachat`

## Goal

Add first-class SDK support for `response_format` in `/chat/completions` requests (sync/async/stream) with a typed API and predictable on-wire serialization.

## Current status (2026-02-16): `$defs` / `$ref` experiments

- Local `$defs` + JSON Pointer `$ref` (including nested `#/$defs/A/$defs/B`) are **accepted by the server**.
- `$ref` support is **partial/unstable** in practice:
  - `$ref` with sibling keywords is not reliably enforced.
  - `$id` + relative refs and `$anchor` refs are not reliable (do not depend on them).
- `strict=true` is **best-effort**, not a hard server guarantee (the response may still be invalid JSON).

Implication: for Pydantic-generated schemas we should apply OpenAI-style normalization (inline `$ref` with sibling keywords, etc.) by default.

## Decisions

- **Request field**: add `Chat.response_format`.
- **Supported mode**: `response_format.type == "json_schema"`.
- **`strict`**: optional boolean, forwarded as-is when provided.
- **Passthrough**: if the user provides a raw `dict` schema, the SDK sends it as-is (no rewriting).
- **Pydantic UX (A+)**: if the user provides a Pydantic `BaseModel` or `TypeAdapter` as the schema, the SDK:
  - generates JSON Schema (`model_json_schema()` / `TypeAdapter.json_schema()`),
  - **normalizes it OpenAI-style** (see `openai.lib._pydantic.to_strict_json_schema`):
    - default `additionalProperties: false` for object schemas (unless explicitly set),
    - default `required` from `properties` (unless explicitly set),
    - inline/unravel `$ref` when `$ref` has sibling keywords (resolve only `#/...` refs from the root schema; merge resolved schema + local overrides),
    - recursively normalize `$defs`/`definitions`, `items`, `anyOf`, `allOf` (flatten single-entry `allOf`).
- **Best-effort outputs**: server/model output may be invalid JSON or schema-mismatched even with `strict=true`.
  - parsing helpers (if implemented) treat `message.content` as untrusted and raise on JSON parsing / validation failures.
- **Merge precedence (non-breaking)**:
  - keep current global merge semantics for `additional_fields`,
  - but **special-case `response_format`**: if `Chat.response_format` is set, it wins over `additional_fields["response_format"]`.

## Minimal wire shape (reference)

```json
{
  "response_format": {
    "type": "json_schema",
    "schema": { "type": "object", "properties": { "x": { "type": "string" } } },
    "strict": true
  }
}
```

## Implementation plan (order)

1. **Models**: add `src/gigachat/models/response_format.py`.
   - `JsonSchemaResponseFormat(type="json_schema", schema, strict?)`
   - `ResponseFormat` (union/alias used by `Chat`)
   - validation: `type="json_schema"` requires `schema` to be an object/dict.
2. **Chat field**: add `response_format: ResponseFormat | None` to `src/gigachat/models/chat.py::Chat`.
3. **Schema generation (A+)**: allow `schema` to accept:
   - `dict[str, Any]` (passthrough),
   - `type[pydantic.BaseModel]`,
   - `pydantic.TypeAdapter[Any]`.
4. **Schema normalization (OpenAI-style)**: implement an internal helper used only for generated schemas.
   - deterministic recursion over `$defs`/`definitions`, `properties`, `items`, `anyOf`, `allOf`,
   - `$ref` resolution limited to `#/...` and performed against the root schema,
   - inline `$ref` only when `$ref` has sibling keys.
5. **Payload construction**: update `src/gigachat/api/chat.py` (both `_get_chat_kwargs` and `_get_stream_kwargs`) to enforce:
   - `Chat.response_format` overrides `additional_fields["response_format"]` when both are present,
   - everything else preserves existing behavior.
6. **Docs**: update `README.md` with a minimal structured output example and a note that the model returns JSON as a string in `message.content`.
7. **Optional helper (B)**: add `chat_parse(...)` / `achat_parse(...)`:
   - sets `response_format` from `response_model`,
   - calls `chat()/achat()`,
   - parses JSON + validates into the model,
   - raises on invalid JSON, model validation failure, and `finish_reason == "length"` / `"content_filter"` (if present).

## Unit tests (must have)

- **Wire serialization**:
  - `response_format` is included in sync request body.
  - `response_format` is included in streaming request body.
  - `strict` is forwarded when set.
- **Validation**:
  - invalid `response_format` shape raises `ValidationError` (e.g., missing `schema` for `type="json_schema"`).
- **Precedence**:
  - when both `Chat.response_format` and `additional_fields["response_format"]` are set, the typed field wins.
- **A+ conversion**:
  - `schema=MyModel` and `schema=TypeAdapter(...)` serialize into a dict schema.
- **Normalization**:
  - `$ref` with sibling keywords is inlined deterministically (OpenAI-style behavior).
- **(If B is implemented)**:
  - invalid JSON raises a dedicated error (or a clear exception type),
  - schema mismatch raises a validation error,
  - `finish_reason` error cases raise.

# Add `response_format` (JSON Schema) support to `gigachat`

## Goal

Add first-class SDK support for `response_format` in `/chat/completions` requests (sync/async/stream) with a typed API and predictable on-wire serialization.

## Decisions (what we will implement)

- **Request field**: add `Chat.response_format`.
- **Supported mode**: `response_format.type == "json_schema"`.
- **`strict`**: optional boolean, forwarded as-is when provided.
- **Passthrough**: if the user provides a raw `dict` schema, the SDK sends it as-is (no rewriting).
- **Pydantic UX (A+)**: if the user provides a Pydantic `BaseModel` or `TypeAdapter` as the schema, the SDK:
  - generates JSON Schema (`model_json_schema()` / `TypeAdapter.json_schema()`),
  - **normalizes it OpenAI-style** (see `openai.lib._pydantic.to_strict_json_schema`):
    - default `additionalProperties: false` for object schemas (unless explicitly set),
    - default `required` from `properties` (unless explicitly set),
    - **inline/unravel `$ref` when `$ref` has sibling keywords** (resolve only `#/...` refs from the root schema; merge resolved schema + local overrides),
    - recursively normalize `$defs`/`definitions`, `items`, `anyOf`, `allOf` (flatten single-entry `allOf`).
- **Best-effort outputs**: the server/model may still return invalid JSON or schema-mismatched JSON even with `strict=true`.
  - parsing helpers (if implemented) must treat `message.content` as untrusted and **raise** on JSON parsing / validation failures.
- **Merge precedence (non-breaking)**:
  - keep current global merge semantics for `additional_fields`,
  - but **special-case `response_format`**: if `Chat.response_format` is set, it wins over `additional_fields["response_format"]`.

## Minimal wire shape (reference)

```json
{
  "response_format": {
    "type": "json_schema",
    "schema": { "type": "object", "properties": { "x": { "type": "string" } } },
    "strict": true
  }
}
```

## Implementation plan (order)

1. **Models**: add `src/gigachat/models/response_format.py`.
   - `JsonSchemaResponseFormat(type="json_schema", schema, strict?)`
   - `ResponseFormat` (union/alias used by `Chat`)
   - validation: `type="json_schema"` requires `schema` to be an object/dict.
2. **Chat field**: add `response_format: ResponseFormat | None` to `src/gigachat/models/chat.py::Chat`.
3. **Schema generation (A+)**: allow `schema` to accept:
   - `dict[str, Any]` (passthrough),
   - `type[pydantic.BaseModel]`,
   - `pydantic.TypeAdapter[Any]`.
4. **Schema normalization (OpenAI-style)**: implement an internal helper used only for generated schemas.
   - deterministic recursion over `$defs`/`definitions`, `properties`, `items`, `anyOf`, `allOf`,
   - `$ref` resolution limited to `#/...` and performed against the root schema,
   - inline `$ref` only when `$ref` has sibling keys.
5. **Payload construction**: update `src/gigachat/api/chat.py` (both `_get_chat_kwargs` and `_get_stream_kwargs`) to enforce:
   - `Chat.response_format` overrides `additional_fields["response_format"]` when both are present,
   - everything else preserves existing behavior.
6. **Docs**: update `README.md` with a minimal structured output example and a note that the model returns JSON as a string in `message.content`.
7. **Optional helper (B)**: add `chat_parse(...)` / `achat_parse(...)`:
   - sets `response_format` from `response_model`,
   - calls `chat()/achat()`,
   - parses JSON + validates into the model,
   - raises on invalid JSON, model validation failure, and `finish_reason == "length"` / `"content_filter"` (if present).

## Unit tests (must have)

- **Wire serialization**:
  - `response_format` is included in sync request body.
  - `response_format` is included in streaming request body.
  - `strict` is forwarded when set.
- **Validation**:
  - invalid `response_format` shape raises `ValidationError` (e.g., missing `schema` for `type="json_schema"`).
- **Precedence**:
  - when both `Chat.response_format` and `additional_fields["response_format"]` are set, the typed field wins.
- **A+ conversion**:
  - `schema=MyModel` and `schema=TypeAdapter(...)` serialize into a dict schema.
- **Normalization**:
  - `$ref` with sibling keywords is inlined deterministically (OpenAI-style behavior).
- **(If B is implemented)**:
  - invalid JSON raises a dedicated error (or a clear exception type),
  - schema mismatch raises a validation error,
  - `finish_reason` error cases raise.

# Plan: add `response_format` (JSON Schema) support to `gigachat`

## Goal

Add support for the `response_format` parameter to `gigachat` chat completions so users can **force the model to answer in JSON** that conforms to a provided JSON Schema (as in the example below).

Key requirements: the SDK must **accept `response_format` in the request payload**, correctly **serialize it into `/chat/completions` requests** (sync/async/stream), and remain **fully typed** (Pydantic v2 + mypy strict).

## Wire format example (raw JSON request/response)

Below is an example of what the API request and response look like when using `response_format` with `type="json_schema"`.

### Request example

```json
{
  "model": "GigaChat-2-Max",
  "messages": [
    {
      "role": "system",
      "content": "Ты — полезный репетитор по математике. Объясняй решение пошагово."
    },
    {
      "content": "Как решить уравнение 8x + 7 = -23. Решай в десятичных числах.",
      "role": "user"
    }
  ],
  "response_format": {
    "type": "json_schema",
    "schema": {
      "type": "object",
      "properties": {
        "steps": {
          "items": {
            "type": "string"
          },
          "title": "Steps",
          "type": "array"
        },
        "final_answer": {
          "title": "Final Answer",
          "type": "string"
        }
      },
      "required": ["steps", "final_answer"]
    },
    "strict": false
  }
}
```

### Response example

Important: the model returns JSON as a **string** in `choices[0].message.content`. In the base API, the SDK does not parse it automatically—this is what the `.chat_parse()` helper (option B) is for.

```json
{
  "choices": [
    {
      "message": {
        "content": "{\n    \"steps\": [\n        \"Исходное уравнение: $8x + 7 = -23$\",\n        \"Шаг 1: Переносим число 7 из левой части уравнения в правую часть, меняя знак числа на противоположный.\",\n        \"Получаем: $8x = -23 - 7$.\",\n        \"Выполняем вычитание справа: $-23 - 7 = -30$, получаем уравнение: $8x = -30$.\",\n        \"Шаг 2: Делим обе стороны уравнения на коэффициент перед x, чтобы найти значение x.\",\n        \"Делим $-30$ на $8$: $x = \\\\frac{-30}{8}$.\"\n    ],\n    \"final_answer\": \"$x = -3.75$\"\n}",
        "role": "assistant"
      },
      "index": 0,
      "finish_reason": "stop"
    }
  ],
  "created": 1771236839,
  "model": "GigaChat-2-Max:2.0.30.01",
  "object": "chat.completions",
  "usage": {
    "prompt_tokens": 56,
    "completion_tokens": 174,
    "total_tokens": 230,
    "precached_prompt_tokens": 5
  }
}
```

## Notes on current architecture (to keep the plan precise)

- The request body is produced from the `Chat` model (`src/gigachat/models/chat.py`) via `chat.model_dump(exclude_none=True, by_alias=True, ...)`.
- Any “non-standard” fields can already be passed via `Chat.additional_fields`, which are merged into the payload in `src/gigachat/api/chat.py` (see `_get_chat_kwargs` / `_get_stream_kwargs`).
- The public client API accepts `payload: Union[Chat, Dict[str, Any], str]` and always runs `Chat.model_validate(payload)` for dict payloads (`src/gigachat/client.py::_parse_chat`).

Conclusion: `response_format` can already be passed “minimally” through `additional_fields`, but proper library support means: a typed field on `Chat`, docs/examples, tests, and a clear precedence rule when `additional_fields` conflicts with typed fields.

## Requirements / Definition of Done

- **Users can pass `response_format`**:
  - as part of `Chat(...)` (typed),
  - as part of a dict payload passed to `client.chat({...})` (validated by Pydantic).
- **`response_format` is included in the JSON request body** sent to `/chat/completions`:
  - sync (`chat.chat_sync`),
  - async (`chat.chat_async`),
  - streaming (`chat.stream_sync` / `chat.stream_async`).
- **No breaking changes** for existing `additional_fields` users.
- **Tests** cover serialization and merge precedence rules.
- **Docs/examples** show that the response comes back as a JSON string in `choices[0].message.content` (as above), and how to parse it.

## API design (what exactly we add)

### 1) Pydantic models for `response_format`

Add a new module, e.g. `src/gigachat/models/response_format.py`:

- `JsonSchemaResponseFormat`:
  - `type`: Literal["json_schema"]
  - `schema`: `Dict[str, Any]` (raw JSON Schema, as in the example)
  - `strict`: `bool | None` (optional; omit from payload when not set)
- `ResponseFormat`: `Union[JsonSchemaResponseFormat, Dict[str, Any]]` (optional; see below)

Why a separate file: keep `models/chat.py` smaller and prepare for future extensions (if new `type` values appear, e.g. `"json_object"`).

Validation:
- Ensure that when `type="json_schema"`, `schema` is provided and is an object.
- Allow a “passthrough mode”: if the user passes a plain dict (not a model), accept it as-is (but preferably validate the known format when `type == "json_schema"`).

### 2) `response_format` field on `Chat`

In `src/gigachat/models/chat.py`, add a new field to `Chat`:

- `response_format: Optional[ResponseFormat] = Field(default=None, description="Response format (e.g. JSON schema).")`

Notes:
- It must serialize as `"response_format"` (field name matches; no alias needed).
- It must be included automatically in `model_dump(exclude_none=True, by_alias=True, ...)`.

### 2.1) OpenAI-style: pass Pydantic models instead of raw JSON Schema (A+)

In the OpenAI Python SDK, you can pass a **Pydantic model directly**, and the SDK will generate JSON Schema and send it as `response_format`.
To provide the same UX in `gigachat`, extend `JsonSchemaResponseFormat.schema` to accept:

- `Dict[str, Any]` — raw JSON Schema (as in the request example)
- `type[pydantic.BaseModel]` — a Pydantic model class
- `pydantic.TypeAdapter[Any]` — for schemas built from `Union[...]`, `Annotated[...]`, etc.

Then, in a `model_validator(mode="before")`, automatically convert them into a dict schema via:

- `model.model_json_schema()` (for `BaseModel`)
- `type_adapter.json_schema()` (for `TypeAdapter`)

On the wire, the format remains the same: `{"type":"json_schema","schema":{...},...}`.

Note: Pydantic schemas often contain `anyOf`/`oneOf`/`allOf` (e.g. for `Union[...]`).
**GigaChat supports `anyOf`/`oneOf` in `response_format=json_schema` mode**, so `Union[...]`-based models can be used directly.
Recommendation (optional): for readability/debuggability, it can be helpful to use discriminated unions (tag field), especially when there are many branches.

#### 2.1.1) IMPORTANT: `$defs` / `$ref` compatibility check (required)

Pydantic V2 will often emit JSON Schema with `$defs` + `$ref` references (especially for nested models).
We **must verify** that the GigaChat API accepts schemas containing `$defs` / `$ref` inside `response_format.schema`.

If the API rejects `$ref`/`$defs` (or supports them only partially), we need a **normalization step** before sending the schema:

- Inline / resolve `$ref` references into concrete schemas (similar to OpenAI SDK behavior).
- Optionally remove `$defs` after inlining, producing a self-contained schema dict.

This check should be done early (before shipping A+), because it affects the on-wire schema we generate.

### 3) Precedence rules when `additional_fields` conflicts

Currently, `additional_fields` are merged last:

```python
json_data = chat.model_dump(...)
fields = json_data.pop("additional_fields", None)
if fields:
    json_data = {**json_data, **fields}
```

This means `additional_fields` **overrides** any same-name fields (including the future `response_format`).

We must make this explicit and document it, but note that changing precedence globally is a **breaking change**.

Two options:

- **Option (safe / non-breaking, recommended initially)**:
  - Keep the current global merge rule (`additional_fields` overrides typed fields).
  - Add a *special-case precedence* for `response_format`:
    - if `Chat.response_format is not None`, then ignore `additional_fields["response_format"]` (and optionally log a warning).
  - Rationale: existing users may rely on `additional_fields` overriding typed fields like `model`, `temperature`, etc.

- **Option (clean but breaking, for a major bump)**:
  - Flip merge precedence globally so typed fields override `additional_fields`:
    - `json_data = {**fields, **json_data}`
  - Add a warning (or release-note callout) for overlapping keys.

Tests must cover whichever rule we pick (see below).

### 3.1) OpenAI-style: `.parse()` helper for automatic response parsing (B)

The OpenAI Python SDK provides this via `client.chat.completions.parse(...)`: you pass a Pydantic model, and get `message.parsed` on output.
To enable OpenAI-style agents in `gigachat`, add a similar helper method (not replacing `chat()`, but alongside it).

Proposed API (roughly):

- `GigaChatSyncClient.chat_parse(payload: Union[Chat, Dict[str, Any], str], *, response_model: type[BaseModel], strict: bool | None = None) -> tuple[ChatCompletion, BaseModel]`
- `GigaChatAsyncClient.achat_parse(...) -> tuple[ChatCompletion, BaseModel]`

Helper behavior:
- set `Chat.response_format` to `json_schema` with schema derived from `response_model`
- call the regular `chat()/achat()`
- parse `message.content` via `json.loads(...)` and validate via `response_model.model_validate(obj)`
- return `(completion, parsed)` (or a specialized `ParsedChatCompletion` if we want to mirror OpenAI more closely)

OpenAI parity notes (behavior to emulate where possible):
- If `finish_reason` is `"length"`: raise a dedicated error (OpenAI: `LengthFinishReasonError`) because JSON may be truncated.
- If `finish_reason` is `"content_filter"`: raise a dedicated error (OpenAI: `ContentFilterFinishReasonError`).
- Only parse when there is content and there is no refusal-like signal. (GigaChat response format may differ; document the exact behavior.)

Why this is useful:
- users do not have to write `json.loads(...)` + `model_validate(...)` themselves
- invalid JSON / schema-mismatch errors become consistent and testable
- you can build agent loops around a “typed step” object, like in the OpenAI agent example

### 3.2) OpenAI-style: schema “strictification” helper (optional but useful)

The OpenAI Python SDK uses an internal helper (`to_strict_json_schema`) that:
- generates JSON Schema from Pydantic (`model_json_schema()` / `TypeAdapter.json_schema()`)
- **inlines** `$ref` when it appears alongside other keys (e.g. `{"$ref": "...", "description": "..."}`) to avoid invalid schemas
- optionally enforces stricter object constraints (e.g. `additionalProperties: false`), depending on server requirements

For `gigachat`, we should implement a small internal helper used by A+/B that at minimum:
- can inline `$ref` references using the root schema as the resolver
- can keep `$defs` intact or remove them after inlining (depending on what the API accepts)

Whether we should enforce `additionalProperties: false` automatically depends on what the GigaChat server expects. Do not assume.

## File-level changes (concrete list)

### Models

- `src/gigachat/models/response_format.py` (new):
  - `JsonSchemaResponseFormat`
  - optionally `ResponseFormat` (type alias/union)
- `src/gigachat/models/chat.py`:
  - add the `response_format` field to `Chat`
- `src/gigachat/models/__init__.py`:
  - export new models (if the project exposes models publicly)

### API layer (payload construction)

- `src/gigachat/api/chat.py`:
  - update the `additional_fields` merge logic so `Chat` fields take precedence
  - ensure this works the same way in `_get_chat_kwargs` and `_get_stream_kwargs`

### Documentation / examples

- `README.md`:
  - add a short “Structured output (JSON Schema)” section near the chat examples
  - emphasize that the API returns JSON as a **string** in `message.content`, and show `json.loads(...)`
- `examples/` (if present in the repository; README links to it):
  - add `examples/response_format_json_schema.py` with a simplified version of the example
  - add `examples/agent_structured_step.py` — an “OpenAI-like” agent loop implemented with `gigachat`

## Test plan (unit + integration if needed)

### 1) Payload serialization test (sync)

Add a test to `tests/unit/gigachat/api/test_chat.py` similar to `test_chat_sync_additional_fields`:

- build a `Chat(...)` with `response_format=...`
- call `chat.chat_sync(...)` with `httpx_mock`
- parse the request body and assert:
  - `request_content["response_format"]["type"] == "json_schema"`
  - `request_content["response_format"]["schema"] == ...`
  - `request_content["response_format"].get("strict") == False` (if provided)

### 2) Payload serialization test (stream)

Add an equivalent test for `chat.stream_sync(...)` and `chat.stream_async(...)`:
- assert that `request_content["response_format"]` is present in the streaming request body.

### 3) Model validation test

In `tests/unit/gigachat/models/test_chat.py` or a separate `test_response_format.py`:

- `Chat.model_validate({... "response_format": {...}})` succeeds
- an invalid case (e.g., `type="json_schema"` without `schema`) raises `ValidationError` (if we enforce strict validation)

### 4) `additional_fields` precedence test

Add a test that builds a `Chat` with:
- `response_format` (explicit field)
- `additional_fields={"response_format": {"type": "json_schema", "schema": {"type": "object", ...}, "strict": True}}` (conflict)

Then assert that the final request body keeps the **value from `Chat.response_format`**, not the one from `additional_fields`.

### 4.1) Tests for Pydantic → JSON Schema (A+)

Add unit tests for `JsonSchemaResponseFormat`:
- `schema=MyPydanticModel` is converted into a `dict` schema in `model_dump(...)`
- `schema=TypeAdapter(Union[...])` is converted into a `dict` schema (if supported)

### 4.1.1) Tests for `$defs` / `$ref` handling (required)

Add tests covering nested Pydantic models that produce `$defs` / `$ref`:
- Verify what is emitted by Pydantic (`model_json_schema()`).
- If we add a normalization/inlining helper, test that:
  - `$ref` with sibling keys is inlined correctly
  - schemas remain JSON-serializable
  - behavior is deterministic

If the API requires *no refs*, add a test asserting the final schema contains no `$ref`.

### 4.2) Tests for `.chat_parse()` / `.achat_parse()` (B)

Add unit tests for the helper methods:
- the SDK sends `response_format` with schema derived from `response_model`
- the SDK parses `message.content` into `response_model` correctly
- errors are raised for:
  - non-JSON content
  - JSON that fails `model_validate`
  - `finish_reason == "length"` (if present) → dedicated error
  - `finish_reason == "content_filter"` (if present) → dedicated error

### 5) Integration (optional)

If the project has VCR integration tests (`tests/integration/test_chat_vcr.py`):
- add a new cassette demonstrating a structured output response
- this is useful, but may require real credentials and cassette updates, so it can be a second phase

## Compatibility & limitations (document upfront)

- `response_format` affects **how the model produces `message.content`**, but the base SDK does not automatically unpack it.
  - As a follow-up (or as part of option B), add a helper like `parse_content_as_json()` / `.chat_parse()`.
- Some models / API versions may not support `response_format`:
  - the server will return HTTP 400; the SDK should raise `BadRequestError` (already implemented).
- For streaming: the model may emit JSON in pieces; the user must accumulate the full `content` before parsing.
- Structured output is best-effort: the server/model may still produce **invalid JSON** (or JSON that does not conform to the schema), regardless of `strict` and schema complexity.
  - The SDK must treat `message.content` as untrusted text and, in parsing helpers (option B), **raise an exception** on `JSONDecodeError` and/or schema validation failures.
- **Pydantic schema refs**: Pydantic may generate `$defs` / `$ref`. In practice, `$ref` handling can be incomplete (e.g., `$ref` with sibling keywords, `$id` resolution, anchors).
  - Decision: follow the OpenAI Python SDK approach and apply an **OpenAI-style schema normalization step** for Pydantic/TypeAdapter-derived schemas (see `openai.lib._pydantic.to_strict_json_schema`):
    - add `additionalProperties: false` for object schemas (unless explicitly set),
    - make `properties` required by default (unless explicitly set),
    - inline/unravel `$ref` when `$ref` appears alongside sibling keywords (merge resolved schema + local overrides),
    - recursively normalize `$defs`/`definitions`, `items`, `anyOf`, `allOf` (including flattening `allOf` with a single element).
  - This normalization is applied when the user passes a Pydantic model / `TypeAdapter` as schema; if the user passes a plain `dict` schema, we keep it as-is ("passthrough mode").

## Execution order (steps)

1. **Design the `response_format` models** (at minimum: `json_schema`) and add the new module under `src/gigachat/models/`.
2. **Extend `Chat`** by adding the `response_format` field.
3. **Implement OpenAI-style schema normalization** for Pydantic/TypeAdapter-derived schemas (inline `$ref` with sibling keywords, `additionalProperties: false`, etc.).
4. **Verify `$defs` / `$ref` acceptance** (quick integration check if possible) and validate that normalization removes known incompatibilities (especially `$ref` with sibling keywords).
5. **Update the `additional_fields` merge** in `src/gigachat/api/chat.py` (both sync and streaming) according to the chosen precedence rule (recommended: special-case for `response_format` first; global change later).
6. **Add unit tests** for:
   - `response_format` serialization in sync/async/stream requests,
   - validation,
   - `additional_fields` vs typed field conflicts.
7. **Implement parsing helper error behavior** (option B): treat `message.content` as untrusted and **raise** on invalid JSON and schema validation failures (even if `strict=true` was requested).
8. **Update README + add examples** under `examples/`.
9. Run local checks:
   - `uv run ruff check .`
   - `uv run ruff format .`
   - `uv run mypy src/gigachat`
   - `uv run pytest`

## TODO (step-by-step implementation checklist)

- [x] **`response_format` models (minimal wire shape)**:
  - [x] Add `src/gigachat/models/response_format.py` with `JsonSchemaResponseFormat(type="json_schema", schema, strict?)`.
  - [x] Add `ResponseFormat` (union/alias) and export it from `src/gigachat/models/__init__.py` if needed.
  - [x] Add validation: when `type="json_schema"`, require `schema` to be an object.

- [x] **Field on `Chat`**:
  - [x] Add `response_format` to `src/gigachat/models/chat.py::Chat`.
  - [x] Ensure `model_dump(exclude_none=True)` serializes `response_format` correctly.

- [x] **A+ (Pydantic/TypeAdapter passed as schema directly)**:
  - [x] Allow `schema` to be `dict | type[BaseModel] | TypeAdapter`.
  - [x] In `model_validator(mode="before")`, convert:
    - [x] `BaseModel` → `model_json_schema()`
    - [x] `TypeAdapter` → `json_schema()`
  - [x] Normalize Pydantic-generated schema using an OpenAI-style helper (`src/gigachat/models/_schema_normalize.py`):
    - [x] apply `additionalProperties: false` defaults for objects,
    - [x] set `required` from `properties` by default,
    - [x] inline/unravel `$ref` when `$ref` has sibling keywords (resolve `#/...` refs from the root schema),
    - [x] recursively normalize `$defs`/`definitions`, `items`, `anyOf`, `allOf` (flatten single-entry `allOf`).
  - [x] Document explicitly: `anyOf/oneOf` are supported (Union works).
  - [ ] **Verify `$defs` / `$ref` compatibility** with the GigaChat server (before/after normalization) and decide if we should additionally inline/remove `$defs` entirely on the wire.

- [x] **Payload building & `additional_fields` precedence**:
  - [x] Choose precedence strategy:
    - [x] (Recommended first) special-case: `Chat.response_format` overrides `additional_fields["response_format"]` if both set.
    - [ ] (Later / major bump) flip global merge so typed fields override `additional_fields`.
  - [x] Verify it works consistently for sync and streaming (`_get_chat_kwargs` and `_get_stream_kwargs`).

- [x] **Unit tests: wire serialization**:
  - [x] `tests/unit/gigachat/api/test_chat.py`: `response_format` is included in sync request body.
  - [x] `tests/unit/gigachat/api/test_chat.py`: `response_format` is included in streaming request body.
  - [x] Conflict test: `additional_fields["response_format"]` vs `Chat.response_format` (the `Chat` field wins).

- [x] **Unit tests: A+ (Pydantic → schema)**:
  - [x] `schema=MyModel` serializes correctly into a dict schema.
  - [x] `schema=TypeAdapter(Union[...])` serializes correctly into a dict schema.
  - [x] Nested model schema includes `$defs` / `$ref` and we handle it correctly (inlined when sibling keys present, preserved when bare).

- [x] **B (OpenAI-style `.parse` helper)**:
  - [x] Add `GigaChatSyncClient.chat_parse(...)` and `GigaChatAsyncClient.achat_parse(...)`:
    - [x] automatically set `response_format` from `response_model`
    - [x] call `chat()/achat()`
    - [x] parse `message.content` into `response_model`
  - [x] Define error behavior (non-JSON / model validation failure) and implement exceptions/messages.
  - [x] Match OpenAI behavior for `finish_reason == "length"` / `"content_filter"` if applicable.

- [x] **Unit tests: B helper**:
  - [x] Happy path: returns `(completion, parsed)` and `parsed` is of the expected type.
  - [x] Error path: non-JSON content → error.
  - [x] Error path: JSON fails `model_validate` → error.

- [x] **Documentation & examples**:
  - [x] `README.md`: `response_format=json_schema` + `json.loads` example.
  - [x] `README.md`: A+ example (pass a Pydantic model as schema).
  - [x] `README.md`: B example (`chat_parse`) — “like OpenAI parse”.
  - [x] `examples/response_format_json_schema.py`.
  - [x] `examples/agent_structured_step.py` (OpenAI-style agent loop).

- [ ] **Integration VCR cassettes (re-record after request shape changes)**:
  - [ ] VCR matches on request `body` and uses `record_mode="once"` (`tests/integration/conftest.py`), so adding new request fields (e.g. `response_format`) requires updating cassettes.
  - [ ] Delete affected cassette(s) under `tests/integration/cassettes/` (at least:
    - `test_chat_simple.yaml`
    - `test_achat_simple.yaml`
    - `test_stream_simple.yaml`
    - `test_astream_simple.yaml`
    )
    and re-run integration tests with real `GIGACHAT_CREDENTIALS` to recreate them.
  - [ ] Review the new cassette contents (tokens must be scrubbed; `expires_at` is set to a far-future timestamp during recording).

- [ ] **Final quality validation**:
  - [ ] `uv run ruff check .`
  - [ ] `uv run ruff format .`
  - [ ] `uv run mypy src/gigachat`
  - [ ] `uv run pytest`

## Minimal usage example (for README / examples)

```python
import json
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

chat = Chat(
    model="GigaChat-2-Max",
    messages=[
        Messages(role=MessagesRole.SYSTEM, content="You are a helpful math tutor. Explain the solution step by step."),
        Messages(role=MessagesRole.USER, content="Solve 8x + 7 = -23. Use decimal numbers."),
    ],
    response_format={
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "steps": {"type": "array", "items": {"type": "string"}},
                "final_answer": {"type": "string"},
            },
            "required": ["steps", "final_answer"],
        },
        "strict": False,
    },
)

with GigaChat() as client:
    resp = client.chat(chat)
    data = json.loads(resp.choices[0].message.content)
    print(data["final_answer"])
```

## Sketch: “agent like OpenAI” (what we want to support)

Goal: enable writing code in the style of `...parse(...)` + “get a typed next-step” + “execute a tool” + “append tool result back to history”, like the OpenAI agent example in [`erc3-agents`](https://github.com/trustbit/erc3-agents/blob/main/sgr-agent-erc3/agent.py).

In `gigachat`, there are two established approaches:

1) **Via the function-calling API (`functions` / `message.function_call`)**: the model returns `function_call`, you execute the function and append a `role="function"` message.
2) **Via structured output (`response_format` + `.chat_parse()`)**: the model returns JSON describing the “next action” (Pydantic), you execute it and append the result back to the conversation.

To best match the OpenAI-style example, we want approach (2) + helper (B), because it lets you describe the “next action” as a single Pydantic model (including `Union[...]` for different tool request models) and get `parsed` without manual JSON parsing.
