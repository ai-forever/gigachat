# GigaChat Examples

Python examples show both supported request styles: SDK models and plain dictionaries.

The examples call `load_dotenv()` on startup, so credentials can be configured either through the environment or an
`.env` file, for example `GIGACHAT_CREDENTIALS` or `GIGACHAT_ACCESS_TOKEN`.

Run Python examples as modules from the repository root:

```bash
uv run python -m examples.chat_completions.sync_chat
```

## Primary chat-completions

* [Sync chat](./chat_completions/sync_chat.py) - `client.chat.create(...)` and `client.chat.stream(...)`
* [Async chat](./chat_completions/async_chat.py) - `GigaChatAsyncClient` with `client.achat.create(...)`
* [Async stream](./chat_completions/async_stream.py) - async SSE stream with `client.achat.stream(...)`
* [Model options](./chat_completions/model_options.py) - temperature, `top_p`, token limits, and usage output
* [Reasoning](./chat_completions/reasoning.py) - `reasoning.effort` for v2 chat requests
* [Thread storage](./chat_completions/thread_storage.py) - reuse `storage.thread_id` between requests

## Structured output

* [Pydantic parse](./structured_outputs/pydantic_parse.py) - `client.chat.parse(...)` with a Pydantic response model
* [JSON Schema](./structured_outputs/json_schema.py) - explicit `response_format.type="json_schema"`
* [Regex format](./structured_outputs/regex_format.py) - constrain output with `response_format.type="regex"`

## Tools

* [Function calling](./tools/function_calling.py) - client function call and follow-up response
* [Forced function call](./tools/forced_function_call.py) - `tool_config.mode="forced"` with a client function
* [Web search](./tools/web_search.py) - built-in `web_search` tool
* [Web search options](./tools/web_search_options.py) - configure built-in web search mode
* [Forced web search](./tools/forced_web_search.py) - force `web_search` through `tool_config.tool_name`
* [Code interpreter](./tools/code_interpreter.py) - built-in `code_interpreter` tool
* [URL content extraction](./tools/url_content_extraction.py) - built-in `url_content_extraction` tool
* [Image generation](./tools/image_generation.py) - built-in `image_generate` tool and generated file IDs

## Files and assistants

* [File input](./files/file_input.py) - `client.files.upload(...)` and file references in message content
* [Assistant lifecycle](./assistants/basic.py) - create, use, and delete an assistant

Notebook examples:

* [Simple Chat](./example_simple_chat.ipynb) - basic chat with system messages and interactive conversation
* [Functions](./example_functions.ipynb) - function calling with the GigaChat API
* [Context Variables](./example_contextvars.ipynb) - optional headers with context variables
* [AI Check](./example_ai_check.ipynb) - detecting AI-generated text with GigaCheckDetection
* [Structured Output](./example_structured_output.ipynb) - structured JSON responses with JSON Schema
* [Vision](./vision/example_vision.ipynb) - image analysis with GigaChat Vision
