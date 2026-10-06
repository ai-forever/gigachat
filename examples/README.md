# GigaChat Examples

Python examples show both supported request styles: SDK models and plain dictionaries.

The examples call `load_dotenv()` on startup, so configuration can be provided either through the environment or an
`.env` file (see `.env.example` in the repository root). Two settings are required:

* credentials, for example `GIGACHAT_CREDENTIALS` or `GIGACHAT_ACCESS_TOKEN`
* `GIGACHAT_MODEL` - the SDK has no default model; examples that do not set a model explicitly rely on this
  variable and raise `ModelNotSpecifiedError` without it (use `client.get_models()` to list available models)

Run Python examples as modules from the repository root:

```bash
uv run python -m examples.chat_completions.sync_chat
```

## Primary chat-completions

* [Sync chat](./chat_completions/sync_chat.py) - `client.chat.create(...)` and `client.chat.stream(...)`
* [Async chat](./chat_completions/async_chat.py) - `GigaChatAsyncClient` with `client.achat.create(...)`
* [Async stream](./chat_completions/async_stream.py) - async SSE stream with `client.achat.stream(...)`
* [Model options](./chat_completions/model_options.py) - temperature, `top_p`, token limits, and usage output
* [Reasoning](./chat_completions/reasoning.py) - separate reasoning and total token budgets, with v1/v2 request builders
* [Thread storage](./chat_completions/thread_storage.py) - reuse `storage.thread_id` and a session header without resending the model
* [Session headers](./chat_completions/session_headers.py) - client default, temporary context override, and restoration
* [Additional fields](./chat_completions/additional_fields.py) - v1/v2 escape hatch with correct wire nesting
* [Response metadata](./chat_completions/response_metadata.py) - ordinary responses, terminal stream metadata, and readable errors

## Structured output

* [Pydantic parse](./structured_outputs/pydantic_parse.py) - `client.chat.parse(...)` with a Pydantic response model
* [JSON Schema](./structured_outputs/json_schema.py) - explicit `response_format.type="json_schema"`
* [Regex format](./structured_outputs/regex_format.py) - constrain output with `response_format.type="regex"`

## Tools

* [Function calling](./tools/function_calling.py) - client function call and follow-up response
* [Parallel function calling](./tools/parallel_function_calling.py) - enable parallel calls and inspect the model's response
* [Parallel function roundtrip](./tools/parallel_function_calling_roundtrip.py) - concurrent local execution, correlated results, and a bounded conversation loop
* [Any function call](./tools/any_function_call.py) - request at least one eligible function with `tool_config.mode="any"`
* [Forced function call](./tools/forced_function_call.py) - `tool_config.mode="forced"` with a client function
* [Web search](./tools/web_search.py) - built-in `web_search` tool
* [Web search options](./tools/web_search_options.py) - configure built-in web search mode
* [Forced web search](./tools/forced_web_search.py) - force `web_search` through `tool_config.tool_name`
* [Code interpreter](./tools/code_interpreter.py) - built-in `code_interpreter` tool
* [URL content extraction](./tools/url_content_extraction.py) - built-in `url_content_extraction` tool
* [Image generation](./tools/image_generation.py) - built-in `image_generate` tool and generated file IDs

## Files and assistants

* [File input](./files/file_input.py) - upload a file and reference it from message content
* [Assistant lifecycle](./assistants/basic.py) - create, use, and delete an assistant

Notebook examples:

* [Simple Chat](./example_simple_chat.ipynb) - basic chat with system messages and interactive conversation
* [Functions](./example_functions.ipynb) - function calling with the GigaChat API
* [Context Variables](./example_contextvars.ipynb) - optional headers with context variables
* [AI Check](./example_ai_check.ipynb) - detecting AI-generated text with GigaCheckDetection
* [Structured Output](./example_structured_output.ipynb) - structured JSON responses with JSON Schema
* [Vision](./vision/example_vision.ipynb) - image analysis with GigaChat Vision

## Try the contract changes

Run any one of these modules after configuring authentication and the model:

```bash
uv run python -m examples.tools.parallel_function_calling_roundtrip
uv run python -m examples.tools.any_function_call
uv run python -m examples.chat_completions.reasoning
uv run python -m examples.chat_completions.model_options
uv run python -m examples.chat_completions.additional_fields
uv run python -m examples.chat_completions.session_headers
uv run python -m examples.chat_completions.thread_storage
uv run python -m examples.chat_completions.response_metadata
```

These scripts make real API requests when run. Tool results are local demonstration
data, not live weather or exchange rates. Reasoning and tool availability depend on
the configured model and API access. No particular cache savings are assumed.

`parallel_tool_calls=True` permits several calls in one response; it does not
guarantee exactly two. The roundtrip example preserves the assistant's calls and
`tools_state_id`, executes local functions concurrently, and returns a separate
`function_result` for each call with the matching `id`. Correlation uses the ID,
including when the same function is called twice. It continues until an assistant
answer is received or the step limit is reached.

`additional_fields` is merged into the HTTP body, not sent as a wrapper. The
example uses ordinary token limits so it can demonstrate the mechanism without
restricted server options; prefer typed fields for normal use. The merge is
shallow, and serialized non-null explicit fields take precedence. Keep advanced
options at their exact API nesting.

The metadata example tolerates chunks without messages, named or unnamed SSE
events, and optional metadata. It prints completion error details separately from
HTTP exceptions. The session example resets its context override in `finally`,
including when a request fails. Stored conversations persist on the server.

Validate the example flows offline, using synthetic HTTP responses:

```bash
uv run pytest -q tests/unit/examples
```

These checks cover SDK serialization and example control flow; they do not certify
a live model's tool selection or feature availability. See the
[migration guide](../MIGRATION_GUIDE.md#additional-contract-support) for field mappings.
