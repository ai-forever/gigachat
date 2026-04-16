# GigaChat Usage Examples

This directory contains examples demonstrating how to use the GigaChat library.

## Notebooks

* [Simple Chat](./example_simple_chat.ipynb) - Basic chat with system messages and interactive conversation
* [Functions](./example_functions.ipynb) - Function calling with the GigaChat API
* [Batching](./example_batching.ipynb) - Creating batch jobs and retrieving their status for asynchronous processing
* [Context Variables](./example_contextvars.ipynb) - Using context variables to pass optional headers (X-Session-ID, X-Request-ID, etc.)
* [AI Check](./example_ai_check.ipynb) - Detecting AI-generated text using GigaCheckDetection model
* [Structured Output](./example_structured_output.ipynb) - Getting structured JSON responses using JSON Schema and `chat_parse()`
* [Vision](./vision/example_vision.ipynb) - Image analysis using GigaChat Vision capabilities

## Scripts

* [Structured Output (JSON Schema)](./response_format_json_schema.py) - Force the model to reply with JSON matching a schema (raw dict, Pydantic model, and `chat_parse()` helper)
* [Agent with Structured Steps](./agent_structured_step.py) - OpenAI-style agent loop using `chat_parse()` and a `Union[...]` response model
* [Validate Function](./validate_function.py) - Check a function schema with `validate_function()` before passing it to chat completions
