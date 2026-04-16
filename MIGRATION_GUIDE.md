# Migration Guide: v1 to v2

This guide explains how to migrate an existing GigaChat Python SDK integration from the v1 chat API to the v2 chat API.

In this repository, "v1" means the classic `chat()` / `stream()` / `achat()` methods built around `Chat`, `Messages`, and `ChatCompletion`, which call `/chat/completions`.

"v2" means the newer `chat_v2()` / `stream_v2()` / `achat_v2()` methods built around `ChatV2`, `ChatV2Message`, `ChatV2ContentPart`, and `ChatCompletionV2`, which call `/api/v2/chat/completions`.

## Who Should Use This Guide

Use this guide if your code currently does one or more of the following:

- Calls `client.chat(...)`, `client.stream(...)`, `client.achat(...)`, or `client.astream(...)`
- Builds request payloads with `Chat` and `Messages`
- Reads responses from `response.choices[0].message`
- Uses v1 `functions` / `function_call`
- Uses `chat_parse()` and wants the v2 equivalent

If you are only using embeddings, files, models, retries, or authentication, those parts of the SDK do not need a migration for v2 chat support.

## What Changes In v2

The biggest differences are structural:

- Requests use `ChatV2` instead of `Chat`
- A message `content` is no longer a plain string; it is a list of structured content parts
- Most generation settings move under `model_options`
- Responses no longer come back as `choices[0].message`; they come back as top-level `messages[]`
- Function calling moves into the v2 `tools` and `tool_config` model
- Streaming emits named SSE events such as `response.message.delta` and `response.message.done`

The authentication model, retry behavior, and client lifecycle stay the same.

## Quick Migration Checklist

1. Replace v1 chat methods with v2 chat methods.
2. Replace `Chat` with `ChatV2`.
3. Replace `Messages(content="...")` with structured `content=[{"text": "..."}]`.
4. Move generation options like `temperature` and `max_tokens` into `model_options`.
5. Update response parsing from `choices[0].message` to `messages[]`.
6. Replace `chat_parse()` with `chat_parse_v2()` if you use structured JSON output.
7. Replace `functions` / `function_call` with `tools` / `tool_config` if you use tool calling.
8. Review any custom `base_url` handling for the v2 endpoint.

## Method Mapping

| v1 | v2 |
|---|---|
| `client.chat(...)` | `client.chat_v2(...)` |
| `client.achat(...)` | `client.achat_v2(...)` |
| `client.stream(...)` | `client.stream_v2(...)` |
| `client.astream(...)` | `client.astream_v2(...)` |
| `client.chat_parse(...)` | `client.chat_parse_v2(...)` |
| `client.achat_parse(...)` | `client.achat_parse_v2(...)` |
| `Chat` | `ChatV2` |
| `Messages` | `ChatV2Message` |
| `ChatCompletion` | `ChatCompletionV2` |
| `ChatCompletionChunk` | `ChatCompletionV2Chunk` |

## Basic Request Migration

### v1

```python
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

chat = Chat(
    messages=[
        Messages(role=MessagesRole.SYSTEM, content="You are a concise assistant."),
        Messages(role=MessagesRole.USER, content="Write a short slogan for a coffee shop."),
    ],
    temperature=0.7,
    max_tokens=200,
)

with GigaChat(credentials="<your_authorization_key>") as client:
    response = client.chat(chat)
    print(response.choices[0].message.content)
```

### v2

```python
from gigachat import GigaChat
from gigachat.models import ChatV2

chat = ChatV2(
    messages=[
        {
            "role": "system",
            "content": [{"text": "You are a concise assistant."}],
        },
        {
            "role": "user",
            "content": [{"text": "Write a short slogan for a coffee shop."}],
        },
    ],
    model_options={
        "temperature": 0.7,
        "max_tokens": 200,
    },
)

with GigaChat(credentials="<your_authorization_key>") as client:
    response = client.chat_v2(chat)
    print("".join(part.text for part in response.messages[0].content if part.text))
```

### What changed

- `Chat` became `ChatV2`
- `Messages.content` changed from `str` to `list[ChatV2ContentPart]`
- `temperature` and `max_tokens` moved under `model_options`
- The response moved from `choices[0].message.content` to `messages[0].content[*].text`

## Request Field Mapping

Use this table when converting typed payloads or raw dict payloads.

| v1 field | v2 field | Notes |
|---|---|---|
| `messages[].role` | `messages[].role` | v2 accepts plain string roles |
| `messages[].content: str` | `messages[].content: [{"text": "..."}]` | v2 content is structured |
| `model` | `model` | Still top-level unless you use `assistant_id` or an existing thread |
| `temperature` | `model_options.temperature` | Moved under `model_options` |
| `top_p` | `model_options.top_p` | Moved under `model_options` |
| `max_tokens` | `model_options.max_tokens` | Moved under `model_options` |
| `repetition_penalty` | `model_options.repetition_penalty` | Moved under `model_options` |
| `update_interval` | `model_options.update_interval` | Moved under `model_options` |
| `unnormalized_history` | `model_options.unnormalized_history` | Moved under `model_options` |
| `top_logprobs` | `model_options.top_logprobs` | Moved under `model_options` |
| `reasoning_effort` | `model_options.reasoning.effort` | Structure changed |
| `response_format` | `model_options.response_format` | Structure moved under `model_options` |
| `function_ranker` | `ranker_options` | Renamed and expanded in v2 |
| `functions` | `tools=[{"functions": {"specifications": [...]}}]` | Tool envelope changed |
| `function_call` | `tool_config` | Use `mode`, `function_name`, or `tool_name` |
| `storage.thread_id` | `storage.thread_id` | Still supported |
| `storage.assistant_id` | `assistant_id` | Moved to top-level |
| `storage.is_stateful` | `storage=True` or `storage={...}` | No direct `is_stateful` field in v2 |
| `messages[].attachments` | `messages[].content[].files` | Files are now content parts |
| `profanity_check` | `disable_filter` | Review `disable_filter` and `filter_config` in v2 |

## Response Mapping

### v1 response shape

```python
message = response.choices[0].message
text = message.content
finish_reason = response.choices[0].finish_reason
prompt_tokens = response.usage.prompt_tokens
completion_tokens = response.usage.completion_tokens
```

### v2 response shape

```python
message = response.messages[0]
text_parts = [part.text for part in message.content if part.text is not None]
text = "".join(text_parts)
finish_reason = response.finish_reason
input_tokens = response.usage.input_tokens
output_tokens = response.usage.output_tokens
cached_tokens = (
    response.usage.input_tokens_details.cached_tokens
    if response.usage and response.usage.input_tokens_details
    else None
)
```

### Response field mapping

| v1 | v2 |
|---|---|
| `response.choices[0].message` | `response.messages[0]` |
| `response.choices[0].message.content` | `response.messages[0].content[*].text` |
| `response.choices[0].message.function_call` | a content part where `part.function_call is not None` |
| `response.choices[0].finish_reason` | `response.finish_reason` |
| `response.usage.prompt_tokens` | `response.usage.input_tokens` |
| `response.usage.completion_tokens` | `response.usage.output_tokens` |
| `response.usage.precached_prompt_tokens` | `response.usage.input_tokens_details.cached_tokens` |

## Streaming Migration

### v1

```python
with GigaChat() as client:
    for chunk in client.stream("Write a haiku about Python"):
        print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### v2

```python
with GigaChat() as client:
    for chunk in client.stream_v2("Write a haiku about Python"):
        if chunk.event == "response.message.delta" and chunk.messages:
            for message in chunk.messages:
                for part in message.content or []:
                    if part.text:
                        print(part.text, end="", flush=True)
```

### Important streaming differences

- v1 streams deltas through `choices[].delta`
- v2 streams named events
- v2 may emit tool-related events like `response.tool.in_progress` and `response.tool.completed`
- The final v2 completion metadata typically arrives in `response.message.done`

If your old stream consumer assumes every chunk only contains text, update it before switching to v2.

## Structured Output Migration

The v1 and v2 SDKs both support JSON Schema based output, but the request location changes.

### v1 with `chat_parse()`

```python
from pydantic import BaseModel
from gigachat import GigaChat


class MathAnswer(BaseModel):
    steps: list[str]
    final_answer: str


with GigaChat() as client:
    completion, parsed = client.chat_parse(
        "Solve 8x + 7 = -23. Explain step by step.",
        response_format=MathAnswer,
        strict=True,
    )

print(parsed.final_answer)
```

### v2 with `chat_parse_v2()`

```python
from pydantic import BaseModel
from gigachat import GigaChat


class MathAnswer(BaseModel):
    steps: list[str]
    final_answer: str


with GigaChat() as client:
    completion, parsed = client.chat_parse_v2(
        "Solve 8x + 7 = -23. Explain step by step.",
        response_format=MathAnswer,
        strict=True,
    )

print(parsed.final_answer)
```

### Manual `response_format` migration

### v1

```python
chat = {
    "messages": [{"role": "user", "content": "Return JSON"}],
    "response_format": {
        "type": "json_schema",
        "schema": MyModel,
        "strict": True,
    },
}
```

### v2

```python
chat = {
    "messages": [{"role": "user", "content": [{"text": "Return JSON"}]}],
    "model_options": {
        "response_format": {
            "type": "json_schema",
            "schema": MyModel,
            "strict": True,
        }
    },
}
```

### Parsing behavior

`chat_parse_v2()` parses the first text-bearing message in the v2 response and raises the same high-level parse exceptions as v1:

- `ContentParseError`
- `ContentValidationError`
- `LengthFinishReasonError`
- `ContentFilterFinishReasonError`

## Function Calling and Tools Migration

v1 uses `functions` and `function_call`.

v2 uses `tools` and `tool_config`.

### v1

```python
from gigachat import GigaChat
from gigachat.models import Chat, Function, FunctionParameters, Messages, MessagesRole

weather_function = Function(
    name="weather-get",
    description="Get weather",
    parameters=FunctionParameters(
        type="object",
        properties={
            "location": {"type": "string", "description": "City name"},
        },
        required=["location"],
    ),
)

chat = Chat(
    messages=[Messages(role=MessagesRole.USER, content="What is the weather in Moscow?")],
    functions=[weather_function],
    function_call="auto",
)

with GigaChat() as client:
    response = client.chat(chat)
    message = response.choices[0].message

    if response.choices[0].finish_reason == "function_call":
        print(message.function_call.name)
        print(message.function_call.arguments)
```

### v2

```python
from gigachat import GigaChat
from gigachat.models import ChatV2, ChatV2Tool, Function, FunctionParameters

weather_function = Function(
    name="weather-get",
    description="Get weather",
    parameters=FunctionParameters(
        type="object",
        properties={
            "location": {"type": "string", "description": "City name"},
        },
        required=["location"],
    ),
)

chat = ChatV2(
    messages=[
        {
            "role": "user",
            "content": [{"text": "What is the weather in Moscow?"}],
        }
    ],
    tools=[ChatV2Tool.functions_tool([weather_function])],
    tool_config={"mode": "auto"},
)

with GigaChat() as client:
    response = client.chat_v2(chat)

    part_with_call = next(
        part
        for message in response.messages
        for part in message.content
        if part.function_call is not None
    )

print(part_with_call.function_call.name)
print(part_with_call.function_call.arguments)
```

### Returning function results back to the model

In v1, function result flows are usually represented with a `role="function"` message.

In v2, return the tool result as a structured content part:

```python
follow_up = ChatV2(
    messages=[
        {
            "role": "tool",
            "tools_state_id": "tool-state-1",
            "content": [
                {
                    "function_result": {
                        "name": "weather-get",
                        "result": {
                            "temperature": 18,
                            "unit": "celsius",
                        },
                    }
                }
            ],
        }
    ]
)
```

Notes:

- Client-defined functions now live inside `tools`
- Internal platform tools such as `web_search` and `image_generate` use the same `tools` list
- Forced tool selection in v2 is configured through `tool_config={"mode": "forced", ...}`

## Stateful Storage and Assistants

v2 changes the shape of stateful conversation settings.

### v1

```python
chat = {
    "messages": [{"role": "user", "content": "Hello"}],
    "storage": {
        "is_stateful": True,
        "limit": 5,
        "assistant_id": "assistant-1",
        "metadata": {"topic": "demo"},
    },
}
```

### v2

```python
chat = {
    "messages": [{"role": "user", "content": [{"text": "Hello"}]}],
    "assistant_id": "assistant-1",
    "storage": {
        "limit": 5,
        "metadata": {"topic": "demo"},
    },
}
```

Important v2 rules:

- `assistant_id` is top-level
- `assistant_id` and `model` are mutually exclusive
- `assistant_id` and `storage.thread_id` are mutually exclusive
- To enable stateful storage without options, you can pass `storage=True`
- When using `assistant_id` or an existing `storage.thread_id`, the SDK does not auto-fill the default model

## Base URL and Endpoint Migration

For v1, the SDK uses the classic chat endpoint under `/chat/completions`.

For v2, the SDK resolves the request URL from `base_url`:

- If `base_url` ends with `/v2`, v2 requests go to `/v2/chat/completions`
- If `base_url` ends with `/v1`, the SDK rewrites it to `/v2/chat/completions`
- If `base_url` already points at `/v2/chat/completions`, it is used directly
- If the SDK cannot derive a v2 URL, it raises `ValueError`

If you use a custom deployment or gateway, set `chat_v2_url_cvar` explicitly:

```python
from gigachat import GigaChat, chat_v2_url_cvar

token = chat_v2_url_cvar.set("https://example.com/custom/api/v2/chat/completions")
try:
    with GigaChat(base_url="https://example.com/api/v1") as client:
        response = client.chat_v2("Hello")
finally:
    chat_v2_url_cvar.reset(token)
```

## Common Pitfalls

### 1. Treating v2 content as a plain string

This is the most common migration bug.

Wrong:

```python
text = response.messages[0].content
```

Correct:

```python
text = "".join(part.text for part in response.messages[0].content if part.text)
```

### 2. Leaving generation options at the top level

Wrong:

```python
chat = {
    "messages": [...],
    "temperature": 0.2,
}
```

Correct:

```python
chat = {
    "messages": [...],
    "model_options": {"temperature": 0.2},
}
```

### 3. Looking for `finish_reason` in `choices[0]`

In v2, `finish_reason` is top-level on the response object.

### 4. Expecting only text during streaming

v2 streams can include tool events and non-text content parts.

### 5. Reusing v1 function-calling assumptions

`functions` and `function_call` are not top-level v2 fields. Move them into `tools` and `tool_config`.

### 6. Using a custom `base_url` that does not end with `/v1` or `/v2`

That works for v1, but v2 URL derivation can fail. Set `chat_v2_url_cvar` explicitly in that case.

## Minimal Before and After

If your old code was this:

```python
from gigachat import GigaChat

with GigaChat(credentials="<your_authorization_key>") as client:
    response = client.chat("Hello!")
    print(response.choices[0].message.content)
```

The smallest v2 version is this:

```python
from gigachat import GigaChat

with GigaChat(credentials="<your_authorization_key>") as client:
    response = client.chat_v2("Hello!")
    print("".join(part.text for part in response.messages[0].content if part.text))
```

## Suggested Migration Strategy

For a production codebase, the safest order is:

1. Switch request builders from `Chat` to `ChatV2`
2. Update response parsing helpers
3. Update streaming consumers
4. Migrate JSON Schema helpers to `chat_parse_v2()`
5. Migrate function calling to `tools`
6. Test any stateful thread or assistant flows
7. Test custom `base_url` deployments

## Summary

The v2 migration is mostly a data-shape migration:

- text messages become structured content parts
- model settings move under `model_options`
- responses move from `choices[].message` to `messages[]`
- tools replace the old function-calling envelope

Once those pieces are updated, the rest of the SDK usage remains familiar: same client lifecycle, same auth setup, same sync and async patterns, and the same high-level parse exception model.
