# Migration Guide to `v2/chat/completions`

This guide covers migration from the previous chat contract to the primary `v2/chat/completions` surface.

In the codebase, `v2` is exposed through explicit resource methods. The previous contract is still available through root compatibility methods.

## TL;DR

1. Use `client.chat(...)` for the previous contract or `client.chat.create(...)` for v2.
2. Use `client.stream(...)` for the previous contract or `client.chat.stream(...)` for v2.
3. Use `client.chat_parse(...)` for the previous contract or `client.chat.parse(...)` for v2.
4. Replace previous-contract models such as `Chat` and `Messages` with primary models such as `ChatCompletionRequest` and `ChatMessage`.
5. Update response access from `response.choices[0].message.content` to primary `messages[*].content[*].text`.

## Why v2 Exists

`v2/chat/completions` is a different contract designed for a broader chat surface:

- richer message content, including multipart content and file references
- stateful conversations through assistants and threads
- a unified model for tool execution, function calling, and structured output
- response metadata that better reflects modern chat flows, including `thread_id`, `tool_execution`, and richer token usage

In the previous contract, the SDK mostly revolved around a single assistant message inside `choices[0].message`. That shape becomes too narrow once the API can return multiple messages, tool state, execution metadata, and multipart content. `v2/chat/completions` makes those concepts first-class instead of hiding them behind compatibility fields.

## What Actually Changed

The migration has three separate layers. Keeping them separate makes upgrades easier:

1. Call site changes
   Replace root compatibility shims with explicit resource methods when you are ready.
2. Payload model changes
   Replace previous-contract request models with primary request models.
3. Response handling changes
   Update code that reads response text, token usage, tool calls, and stream chunks.

If your code only sends a string prompt and prints one text response, migration is small. If you build request payloads directly, parse structured output, or use function calling, you should treat this as a real contract migration rather than a rename.

## API Surface Changes

| Previous call | v2 primary call | If you want previous behavior |
| --- | --- | --- |
| `client.chat(payload)` | `client.chat.create(payload)` | `client.chat(payload)` |
| `client.stream(payload)` | `client.chat.stream(payload)` | `client.stream(payload)` |
| `client.chat_parse(payload, response_format=...)` | `client.chat.parse(payload, response_format=...)` | `client.chat_parse(payload, response_format=...)` |
| `await client.achat(payload)` | `await client.achat.create(payload)` | `await client.achat(payload)` |
| `client.astream(payload)` | `client.achat.stream(payload)` | `client.astream(payload)` |
| `await client.achat_parse(payload, response_format=...)` | `await client.achat.parse(payload, response_format=...)` | `await client.achat_parse(payload, response_format=...)` |

`client.chat(...)`, `client.stream(...)`, `client.chat_parse(...)`, `client.achat(...)`, `client.astream(...)`, and `client.achat_parse(...)` still work as compatibility shims for the previous chat contract. They are not deprecated and do not emit `DeprecationWarning`.

Primary chat completions use the v2 route. If the client `base_url` still ends with `/v1`, `client.chat.create(...)`, `client.chat.stream(...)`, `client.achat.create(...)`, and `client.achat.stream(...)` automatically send requests to the matching `/v2/chat/completions` URL. Explicit `chat_completions_url` overrides are still honored, including versioned paths such as `/v2/chat/completions`.

Why this changed:

- `client.chat` and `client.achat` are now resource namespaces, not just callable shims.
- The resource layout makes the API consistent with other SDK surfaces and leaves room for multiple operations such as `create`, `stream`, and `parse`.
- Root compatibility methods keep the previous contract available while explicit resource methods expose v2.

## Recommended Migration Strategy

For production applications, the safest path is incremental:

1. Move off root compatibility shims when you are ready.
   Move to `client.chat.create()` / `client.chat.stream()` / `client.chat.parse()` first.
2. If you cannot migrate payloads immediately, keep using root compatibility methods.
   This keeps the previous contract available without forcing a full contract rewrite.
3. Migrate request models.
   Replace `Chat` and `Messages` with `ChatCompletionRequest` and `ChatMessage`.
4. Migrate response readers.
   Update all places that read `choices`, `message.content`, `created`, or previous `usage`.
5. Migrate structured output and tool-calling code.
   These areas benefit the most from the primary contract.

This order matters because replacing root shims is mechanical, while response and payload migration usually touches business logic.

## Request Model Migration

The primary request contract is not an extension of the previous one. Complex payloads should be migrated to `ChatCompletionRequest`.

| Previous | v2 primary |
| --- | --- |
| `Chat` | `ChatCompletionRequest` |
| `Messages` | `ChatMessage` |
| `MessagesRole.USER` | `"user"` |
| `response_format` on `Chat` | `model_options.response_format` on `ChatCompletionRequest` |
| plain string `message.content` | `content` normalized to a list of parts |

Why this changed:

- The previous contract modeled messages around a single text field.
- v2 models messages as content parts so the API can carry text, files, tool results, and inline metadata in one structure.
- Some advanced capabilities are now represented as explicit top-level fields such as `assistant_id`, `tool_config`, and `storage`.

Primary-only request capabilities include:

- `assistant_id`
- `tools_state_id`
- multipart `messages[].content`
- `model_options`
- `model_options.reasoning`
- `model_options.response_format`
- `filter_config`
- `storage.thread_id`
- `ranker_options`
- `tool_config`
- `tools`
- `user_info`
- `stream`
- `disable_filter`
- `flags`

### Before

```python
from gigachat.models import Chat, Messages, MessagesRole

payload = Chat(
    messages=[
        Messages(
            role=MessagesRole.USER,
            content="Hello!",
        )
    ]
)

response = client.chat(payload)
```

### After

```python
from gigachat.models import ChatCompletionRequest, ChatMessage

payload = ChatCompletionRequest(
    messages=[
        ChatMessage(
            role="user",
            content="Hello!",
        )
    ]
)

response = client.chat.create(payload)
```

Notes:

- A plain string payload still works: `client.chat.create("Hello!")`.
- Primary message `content` accepts a string, a single object, or a list. The SDK normalizes it to a list of content parts.
- When you call through the client, `model` defaults to `GigaChat` unless you use `assistant_id` or an existing `storage.thread_id`.
- The SDK accepts top-level `response_format` and `reasoning` as convenience inputs on `ChatCompletionRequest`, but serializes them under `model_options`.
- `tools` accepts full tool objects and supported shorthand strings such as `"code_interpreter"`, `"image_generate"`, `"web_search"`, `"url_content_extraction"`, and `"model_3d_generate"`.

### How to Think About `content`

In v1, the common mental model was:

- one message
- one string body

In v2, the mental model is:

- one message
- zero or more content parts

That is why `ChatMessage(content="Hello!")` still works, but internally the SDK normalizes it to something conceptually equivalent to:

```python
[
    {"text": "Hello!"}
]
```

This matters when you later add files, inline metadata, or tool results. You no longer need a second ad hoc structure for those cases.

### Typical v1 to v2 Request Rewrite

If your previous code constructed a request object directly, the migration is usually:

1. Replace `Chat(...)` with `ChatCompletionRequest(...)`.
2. Replace each `Messages(...)` with `ChatMessage(...)`.
3. Convert enum-style roles to string roles.
4. Move any logic that assumes message content is a string to logic that accepts content parts.
5. Rename or rethink previous-contract-only fields instead of copying them mechanically.

The last point is important: v2 is close enough to the previous contract to look familiar, but not close enough for blind field-for-field translation in non-trivial payloads.

## Response Model Migration

The primary response shape is materially different.

| Previous create response | v2 primary response |
| --- | --- |
| `response.choices[0].message.content` | `"".join(part.text or "" for part in assistant_message.content or [])` |
| `response.usage.prompt_tokens` | `response.usage.input_tokens` |
| `response.usage.completion_tokens` | `response.usage.output_tokens` |
| `response.created` | `response.created_at` |
| streaming `chunk.choices` | streaming `chunk.messages` |

Why this changed:

- The previous contract assumed the meaningful answer lives in one place: `choices[0].message`.
- v2 can return message-oriented outputs and tool state at the top level, so `messages` becomes the main response carrier.
- token accounting was renamed to reflect request/response semantics more clearly: `input_tokens` and `output_tokens`.

### Before

```python
text = response.choices[0].message.content
```

### After

```python
message = next(message for message in response.messages if message.role == "assistant")
text = "".join(part.text or "" for part in message.content or [])
```

Primary responses may also include `thread_id`, `tool_execution`, `logprobs`, and opaque `additional_data` entries.

### Why Response Readers Usually Break First

The most common migration bug is not request construction. It is downstream code that assumes:

- `response.choices` always exists
- `message.content` is always a plain string
- `usage.prompt_tokens` and `usage.completion_tokens` exist
- stream chunks look like previous-contract chunks

Search for these patterns when migrating:

- `choices[0]`
- `.message.content`
- `prompt_tokens`
- `completion_tokens`
- `created`

Those are the places most likely to need real logic changes rather than simple renames.

### Recommended Text Extraction Pattern

If your application only needs assistant text, use an explicit helper in your codebase instead of repeating list joins everywhere:

```python
def extract_text(message):
    return "".join(part.text or "" for part in message.content or [])
```

That gives you one place to evolve later if you start handling files or non-text content parts.

## Streaming Migration

Streaming code often needs more than a method rename.

### Before

```python
for chunk in client.stream("Write a poem"):
    if chunk.choices:
        print(chunk.choices[0].delta.content or "", end="")
```

### After

```python
for chunk in client.chat.stream("Write a poem"):
    if chunk.messages and chunk.messages[0].content:
        print("".join(part.text or "" for part in chunk.messages[0].content), end="")
```

Why this changed:

- primary streaming emits message-based chunks
- primary streaming is parsed as named SSE events, so `chunk.event` can be values such as `response.message.delta`, `response.tool.completed`, or `response.message.done`
- final or tool-related chunks can contain only `finish_reason`, `usage`, `tools_state_id`, `tool_execution`, or metadata without text
- tool execution and additional metadata may appear alongside text

Root streaming methods still use the old `data:` line parser and previous chunk model. Primary streaming uses the event-aware parser and does not require a `[DONE]` marker. If your streaming consumer merges partial text, revisit that logic carefully. Previous `delta`-style assumptions do not always map one-to-one to primary `messages`.

## Structured Output Migration

If you previously used the root parse methods, migrate to the primary parse methods when you move to the v2 contract.

### Before

```python
completion, parsed = client.chat_parse(
    "Solve 8x + 7 = -23",
    response_format=MathAnswer,
)
```

### After

```python
completion, parsed = client.chat.parse(
    "Solve 8x + 7 = -23",
    response_format=MathAnswer,
)
```

Important:

- `client.chat.parse()` and `client.achat.parse()` send a primary request with `response_format={"type": "json_schema", ...}`.
- On the wire, that schema is sent as `model_options.response_format`.
- If you want to stay on the previous contract, use `client.chat_parse()` and `client.achat_parse()`.
- Passing a Pydantic model as `response_format` to the previous-contract create path is not the migration path; use `parse()` instead.

Why this is better in v2:

- structured output is part of the primary contract instead of an add-on around the previous response shape
- the SDK parses assistant text from primary `messages`
- the request schema is represented explicitly as `ChatResponseFormat(type="json_schema", ...)`

If you already depend on schema-validated output, migrating parse helpers early usually reduces future churn.

## Tool Calling and Advanced Features

v2 is the better target if your integration uses or plans to use:

- function calling
- built-in tools such as web search
- assistant-based stateful conversations
- thread storage
- richer response metadata

The reason is structural: these features fit naturally into the primary request/response model, while in the previous contract they are either absent, narrower, or modeled in compatibility shapes.

For example, v2 introduces explicit request fields such as:

- `tools`
- `tool_config`
- `assistant_id`
- `storage`
- `ranker_options`
- `user_info`

If your application roadmap includes any of those, migrating only the surface method names and staying on previous-contract payloads is usually a short-lived compromise rather than a final state.

## Model Import Migration

During the transition, existing imports still resolve to compatibility aliases.

| Existing import | What it means now | Recommended replacement |
| --- | --- | --- |
| `from gigachat.models import Chat` | Previous request alias | `from gigachat.models import ChatCompletionRequest` |
| `from gigachat.models import Messages` | Previous message alias | `from gigachat.models import ChatMessage` |
| `from gigachat.models import ChatCompletion` | Previous response alias | `from gigachat.models import ChatCompletionResponse` |
| `from gigachat.models import Usage` | Previous usage alias | `from gigachat.models import ChatUsage` |
| `from gigachat.models import Storage` | Previous storage alias | `from gigachat.models import ChatStorage` |
| `from gigachat.models import ChatCompletionChunk` | Previous stream chunk alias | `from gigachat.models import PrimaryChatCompletionChunk` |
| `from gigachat.models import ChatFunctionCall` | Previous function-call alias | `from gigachat.models import PrimaryChatFunctionCall` |

Use `Primary*` aliases, or direct imports from `gigachat.models.chat_completions`, for primary types whose names collide with compatibility aliases.

Why explicit primary imports matter:

- some top-level names are intentionally kept as aliases for backwards compatibility
- primary aliases and direct imports from `gigachat.models.chat_completions` remove ambiguity
- this is especially important for colliding names such as `ChatCompletionChunk`

If you are doing a broad application migration, updating imports explicitly is often the clearest signal that the codepath now expects the v2 contract.

## Staying on the Previous Contract

Migration is incremental. If you are not ready to move request and response handling yet, keep using root compatibility methods.

```python
response = client.chat(payload)

for chunk in client.stream(payload):
    ...

completion, parsed = client.chat_parse(
    payload,
    response_format=MathAnswer,
)
```

The same pattern applies to async code via `client.achat(...)`, `client.astream(...)`, and `client.achat_parse(...)`.

This is useful when:

- you want to make previous-contract usage explicit first
- your code depends heavily on `choices[0].message.content`
- you have many downstream consumers that still expect previous usage fields or chunk shapes

Treat root compatibility methods as the previous-contract lane, not the long-term direction of new v2 code.

## Migration Checklist

Use this checklist when upgrading an application from v1 to v2:

1. Replace root compatibility methods with explicit resource methods when you are ready.
2. Decide whether each codepath should move to primary now or temporarily stay on root compatibility methods.
3. Replace previous-contract request models with primary models in migrated codepaths.
4. Rewrite response readers from `choices`-based access to `messages`-based access.
5. Update streaming consumers to read primary chunks.
6. Replace compatibility import aliases with explicit primary imports where names collide.
7. Update structured output code to `client.chat.parse()` / `client.achat.parse()`.
8. Re-test any code that depends on tool calling, usage accounting, or timestamp fields.

## Common Migration Mistakes

- Renaming `client.chat(...)` to `client.chat.create(...)` but still reading `response.choices[0].message.content`.
- Importing `ChatCompletionChunk` from `gigachat.models` and expecting the primary chunk shape; use `PrimaryChatCompletionChunk`.
- Treating v2 as a field-for-field extension of the previous payload.
- Moving sync code to `client.chat.create()` but leaving async code on root compatibility shims.
- Passing a Pydantic model to the previous-contract create path instead of switching to `parse()`.

If you see one of those patterns in a code review, the migration is only partial.

## Compatibility Notes

- Primary models are intentionally tolerant and allow extra fields in the wire format.
- `tool_state_id` and `functions_state_id` are accepted as aliases for `tools_state_id`.
- `created` is accepted as an alias for `created_at` in primary responses and chunks.
- Existing top-level imports remain available during migration, but new code should prefer primary names.
