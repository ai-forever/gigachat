# GigaChat Python SDK

[![PyPI version](https://img.shields.io/pypi/v/gigachat?style=flat-square&cacheSeconds=300)](https://pypi.org/project/gigachat/)
[![Python versions](https://img.shields.io/pypi/pyversions/gigachat?style=flat-square&cacheSeconds=300)](https://pypi.org/project/gigachat/)
[![License](https://img.shields.io/github/license/ai-forever/gigachat?style=flat-square)](https://opensource.org/license/MIT)
[![CI](https://img.shields.io/github/actions/workflow/status/ai-forever/gigachat/gigachat.yml?style=flat-square)](https://github.com/ai-forever/gigachat/actions/workflows/gigachat.yml)
[![Downloads](https://static.pepy.tech/badge/gigachat/month)](https://pepy.tech/project/gigachat)

Python SDK for the [GigaChat REST API](https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/gigachat-api) — a large language model.

This library is part of [GigaChain](https://github.com/ai-forever/gigachain) and powers [langchain-gigachat](https://github.com/ai-forever/langchain-gigachat), the official LangChain integration for GigaChat.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
  - [Basic Chat](#basic-chat)
  - [Streaming](#streaming)
  - [Async](#async)
  - [Async With `aiohttp`](#async-with-aiohttp)
  - [Embeddings](#embeddings)
  - [Function Calling](#function-calling)
  - [Structured Output (JSON Schema)](#structured-output-json-schema)
  - [More Examples](#more-examples)
- [Configuration](#configuration)
  - [Constructor Parameters](#constructor-parameters)
  - [Environment Variables](#environment-variables)
- [Authentication](#authentication)
- [SSL Certificates](#ssl-certificates)
- [Error Handling](#error-handling)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)
- [Related Projects](#related-projects)
- [Contributing](#contributing)
- [License](#license)

## Features

- ✅ **Chat completions** — synchronous and asynchronous
- ✅ **Streaming responses** — real-time token generation
- ✅ **Embeddings** — text vectorization
- ✅ **Function calling** — tool use for building agents
- ✅ **Vision** — image understanding (multimodal)
- ✅ **File operations** — upload, retrieve, and delete files
- ✅ **Token counting** — estimate token usage before requests
- ✅ **Multiple auth methods** — OAuth credentials, password, TLS certificates, access tokens
- ✅ **Automatic retry** — configurable exponential backoff for transient errors
- ✅ **Fully typed** — Pydantic V2 models with `py.typed` marker for IDE support

## Installation

```bash
pip install gigachat
```

To use `aiohttp` as the async HTTP backend for async clients:

```bash
pip install gigachat[aiohttp]
```

**Requirements:** Python 3.8 — 3.13

> **Note:** In production, keep TLS verification enabled (default).
> See [SSL Certificates](#ssl-certificates) for setup instructions.

## Quick Start

### Get your GigaChat authorization key

For detailed instructions, see the [official documentation](https://developers.sber.ru/docs/ru/gigachat/quickstart/main).

### Configure gigachat package to use TLS certificate

TLS certificate: follow the OS-specific installation steps on [Gosuslugi](https://www.gosuslugi.ru/crt) (see [SSL Certificates](#ssl-certificates) for how to configure `GIGACHAT_CA_BUNDLE_FILE` / `ca_bundle_file` if needed).

**Development-only (not recommended):**

set `GIGACHAT_VERIFY_SSL_CERTS=false` or pass `verify_ssl_certs=False` to `GigaChat(...)`.

## Usage Examples

> The examples below assume authentication is configured via environment variables (for example, `GIGACHAT_CREDENTIALS`). See [Authentication](#authentication).

### Basic Chat

```python
from gigachat import GigaChat

with GigaChat(credentials="<your_authorization_key>") as client:
    response = client.chat("Hello, GigaChat!")
    print(response.choices[0].message.content)
```

### Streaming

Receive tokens as they are generated:

```python
from gigachat import GigaChat

with GigaChat() as client:
    for chunk in client.stream("Write a short poem about programming"):
        print(chunk.choices[0].delta.content, end="", flush=True)
    print()  # Newline at the end
```

### Async

Use async/await for non-blocking operations:

```python
import asyncio
from gigachat import GigaChat

async def main():
    async with GigaChat() as client:
        # Async chat
        response = await client.achat("Explain quantum computing in simple terms")
        print(response.choices[0].message.content)

        # Async streaming
        print("Streaming response:")
        async for chunk in client.astream("Tell me a joke"):
            print(chunk.choices[0].delta.content, end="", flush=True)
        print()

asyncio.run(main())
```

### Async With `aiohttp`

By default, async requests use `httpx`. For higher-concurrency workloads you can switch the async backend to `aiohttp`.
This option affects async clients only and does not change the synchronous client.

First install the extra:

```bash
pip install gigachat[aiohttp]
```

Then pass `DefaultAioHttpClient()` to `GigaChat(...)`:

```python
import asyncio

from gigachat import DefaultAioHttpClient, GigaChat


async def main() -> None:
    async with GigaChat(
        http_client=DefaultAioHttpClient(),
        max_connections=100,
    ) as client:
        response = await client.achat("Say this is a test")
        print(response.choices[0].message.content)

        print("Streaming response:")
        async for chunk in client.astream("Write one sentence about aiohttp"):
            print(chunk.choices[0].delta.content, end="", flush=True)
        print()


asyncio.run(main())
```

`gigachat[aiohttp]` installs the appropriate dependency for your Python version:

- Python 3.8: `aiohttp`
- Python 3.9+: `httpx-aiohttp`

### Embeddings

Generate vector representations of text:

```python
from gigachat import GigaChat

with GigaChat() as client:
    result = client.embeddings(
        ["Hello, world!", "Machine learning is fascinating"],
        model="Embeddings",
    )

    for i, item in enumerate(result.data):
        print(f"Text {i + 1}: {len(item.embedding)} dimensions")
```

> **Note:** The `model` parameter must be passed directly to the `embeddings()` method (default: `"Embeddings"`).
> The `model` set in the `GigaChat()` constructor does not affect embeddings.

### Function Calling

Enable the model to call functions (tools):

```python
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole, Function, FunctionParameters

weather_function = Function(
    name="get_weather",
    description="Get current weather for a location",
    parameters=FunctionParameters(
        type="object",
        properties={
            "location": {
                "type": "string",
                "description": "City name, e.g., Moscow"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit"
            }
        },
        required=["location"],
    ),
)

chat = Chat(
    messages=[Messages(role=MessagesRole.USER, content="What's the weather in Tokyo?")],
    functions=[weather_function],
)

with GigaChat() as client:
    response = client.chat(chat)
    message = response.choices[0].message

    if response.choices[0].finish_reason == "function_call":
        print(f"Function: {message.function_call.name}")
        print(f"Arguments: {message.function_call.arguments}")
```

### Structured Output (JSON Schema)

Force the model to reply with JSON matching your schema by setting `response_format.type="json_schema"`.

> **Important:** The API returns JSON as a **string** in `choices[0].message.content`.
> You must parse it yourself or use `chat_parse()` (see below).

#### Pass a Pydantic model as schema

You can pass a Pydantic `BaseModel` subclass (or a `TypeAdapter`) directly as `schema`.
The SDK generates the JSON Schema, normalizes it (OpenAI-style: `additionalProperties: false`,
all properties required, `$ref` with sibling keywords inlined), and sends the result on the wire.

```python
import json
from typing import List
from pydantic import BaseModel

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole


class MathAnswer(BaseModel):
    steps: List[str]
    final_answer: str


chat = Chat(
    messages=[
        Messages(role=MessagesRole.USER, content="Solve 8x + 7 = -23. Explain step by step."),
    ],
    response_format={
        "type": "json_schema",
        "schema": MathAnswer,
        "strict": True,
    },
)

with GigaChat() as client:
    resp = client.chat(chat)
    data = json.loads(resp.choices[0].message.content)
    parsed = MathAnswer.model_validate(data)
    print(parsed.final_answer)
```

You can also pass a raw `dict` JSON Schema instead of a Pydantic model — in that case the SDK sends it as-is (no normalization).

Pydantic schemas may include `anyOf` / `oneOf` (for example, when using `Union[...]`). This is supported by the API, so you can model multiple valid JSON shapes and validate the output accordingly.

#### Automatic parsing with `chat_parse()`

Instead of calling `json.loads` + `model_validate` manually, use `chat_parse()` (or `achat_parse()` for async).
It sets `response_format` from the model, calls the API, parses and validates the response in one step:

```python
from typing import List
from pydantic import BaseModel

from gigachat import GigaChat


class MathAnswer(BaseModel):
    steps: List[str]
    final_answer: str


with GigaChat() as client:
    completion, parsed = client.chat_parse(
        "Solve 8x + 7 = -23. Explain step by step.",
        response_model=MathAnswer,
        strict=True,
    )
    print(parsed.steps)
    print(parsed.final_answer)
```

`chat_parse` raises specific exceptions when parsing fails:

| Exception | When |
|-----------|------|
| `ContentParseError` | `message.content` is not valid JSON |
| `ContentValidationError` | JSON does not match `response_model` |
| `LengthFinishReasonError` | `finish_reason == "length"` (response truncated) |
| `ContentFilterFinishReasonError` | `finish_reason == "content_filter"` |

### More examples
See the [examples/](https://github.com/ai-forever/gigachat/tree/main/examples/) folder for complete working examples including chat, functions, context variables, AI detection, and vision.

## Configuration

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `credentials` | `str` | `None` | Authorization key from GigaChat API |
| `scope` | `str` | `GIGACHAT_API_PERS` | API scope (see below) |
| `model` | `str` | `GigaChat` | Default model for requests |
| `base_url` | `str` | `https://gigachat.devices.sberbank.ru/api/v1` | API base URL |
| `auth_url` | `str` | `https://ngw.devices.sberbank.ru:9443/api/v2/oauth` | OAuth token endpoint |
| `access_token` | `str` | `None` | Pre-obtained access token (bypasses OAuth) |
| `user` | `str` | `None` | Username for password authentication |
| `password` | `str` | `None` | Password for password authentication |
| `verify_ssl_certs` | `bool` | `True` | Verify SSL certificates |
| `ca_bundle_file` | `str` | `None` | Path to CA certificate bundle |
| `cert_file` | `str` | `None` | Path to client certificate (for mTLS) |
| `key_file` | `str` | `None` | Path to client private key (for mTLS) |
| `key_file_password` | `str` | `None` | Password for encrypted private key |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `http_client` | `AsyncHttpClientFactory` | `None` | Custom async HTTP backend factory (async clients only) |
| `max_connections` | `int` | `None` | Maximum concurrent connections |
| `max_retries` | `int` | `0` | Maximum retry attempts for transient errors |
| `retry_backoff_factor` | `float` | `0.5` | Exponential backoff multiplier |
| `retry_on_status_codes` | `tuple` | `(429, 500, 502, 503, 504)` | HTTP status codes that trigger retry |
| `profanity_check` | `bool` | `None` | Enable profanity filtering |
| `flags` | `list` | `None` | Additional API flags |

**API Scopes:**

| Scope | Description |
|-------|-------------|
| `GIGACHAT_API_PERS` | API for individuals (default) |
| `GIGACHAT_API_B2B` | API for businesses (prepaid) |
| `GIGACHAT_API_CORP` | API for businesses (postpaid) |

### Environment Variables

All parameters can be configured via environment variables with the `GIGACHAT_` prefix:

```bash
# Authentication
export GIGACHAT_CREDENTIALS="<your_authorization_key>"
export GIGACHAT_SCOPE="GIGACHAT_API_PERS"

# Connection
export GIGACHAT_BASE_URL="https://gigachat.devices.sberbank.ru/api/v1"
export GIGACHAT_TIMEOUT="60.0"
export GIGACHAT_VERIFY_SSL_CERTS="true"
# TLS: path to a CA bundle file (typically required - Python HTTP clients often don't use OS trust store by default)
export GIGACHAT_CA_BUNDLE_FILE="<your_ca_bundle_file>"

# Model
export GIGACHAT_MODEL="GigaChat"

# Retry
export GIGACHAT_MAX_RETRIES="3"
export GIGACHAT_RETRY_BACKOFF_FACTOR="0.5"
```

Then create a client without any parameters:

```python
from gigachat import GigaChat

# Configuration loaded from environment variables
with GigaChat() as client:
    response = client.chat("Hello!")
```

## Authentication

The library supports four authentication methods:

### Authentication priority (when multiple are configured)

If multiple auth inputs are provided at the same time, the SDK applies this priority:

1. **`custom_headers_cvar["Authorization"]`** (if set) — overrides any other auth source.
2. **`authorization_cvar`** (if set) — overrides any other auth source and **disables automatic token fetching/refresh** (you manage the header value and its lifecycle).
3. **Explicit `access_token`** (constructor parameter / `GIGACHAT_ACCESS_TOKEN`) — used as-is. If it fails with 401 and OAuth credentials or user/password are also configured, the SDK will fall back to fetching a new token.
4. **OAuth `credentials`** (constructor parameter / `GIGACHAT_CREDENTIALS`) — used to obtain/refresh a token.
5. **Username/password** (`user` + `password`) — used to obtain/refresh a token from the `/token` endpoint.

When both **OAuth `credentials`** and **username/password** are provided, OAuth credentials take precedence for token refresh.

### 1. Authorization Key (Recommended)

For detailed instructions, see the [official documentation](https://developers.sber.ru/docs/ru/gigachat/quickstart/main).

```python
from gigachat import GigaChat

client = GigaChat(credentials="<your_authorization_key>")
```

The authorization key encodes your API scope. If using the B2B or CORP API, specify the scope explicitly:

```python
client = GigaChat(
    credentials="<your_authorization_key>",
    scope="GIGACHAT_API_B2B",  # or GIGACHAT_API_CORP
)
```

### 2. Username and Password

Authenticate with a username and password:

```python
from gigachat import GigaChat

client = GigaChat(
    base_url="https://gigachat.devices.sberbank.ru/api/v1",
    user="<username>",
    password="<password>",
)
```

### 3. TLS Certificates (mTLS)

Authenticate using client certificates for mutual TLS:

```python
from gigachat import GigaChat

client = GigaChat(
    base_url="https://gigachat.devices.sberbank.ru/api/v1",
    cert_file="certs/client.pem",         # Client certificate
    key_file="certs/client.key",          # Client private key
    key_file_password="<key_password>",   # Optional: password for encrypted key
)
```

### 4. Access Token

Use a pre-obtained access token (JWT):

```python
from gigachat import GigaChat

client = GigaChat(access_token="<your_access_token>")
```

> **Note:** Access tokens expire after 30 minutes. Use this method when you manage token lifecycle externally.

### Pre-authentication

By default, the library obtains an access token on the first API request. To authenticate immediately:

```python
from gigachat import GigaChat

client = GigaChat(credentials="<your_authorization_key>")
token = client.get_token()  # Authenticate now
print(f"Token expires at: {token.expires_at}")
```

## SSL Certificates

GigaChat endpoints use a certificate chain issued by the Russian Ministry of Digital Development.
This section explains how to configure the GigaChat SDK to use the required certificates.

### Quick Reference

- **What you need:** The **"Russian Trusted Root CA"** certificate file from [Gosuslugi](https://www.gosuslugi.ru/crt)
- **How to configure:** Set `GIGACHAT_CA_BUNDLE_FILE` environment variable or pass `ca_bundle_file` argument to `GigaChat()`
- **Why:** Python HTTP clients typically use their own CA bundle (e.g., `certifi`) instead of the OS trust store

### Configuration

**Environment variable (recommended):**

```bash
export GIGACHAT_CA_BUNDLE_FILE="<path_to_root_ca_file>"
```

**Or as argument:**

```python
from gigachat import GigaChat

with GigaChat(ca_bundle_file="<path_to_root_ca_file>") as client:
    response = client.chat("Hello!")
    print(response.choices[0].message.content)
```

### OS-Specific Notes

Download the **"Russian Trusted Root CA"** certificate from [Gosuslugi](https://www.gosuslugi.ru/crt) and configure `GIGACHAT_CA_BUNDLE_FILE` to point to the downloaded file:

- **Windows**: Downloaded as `.cer` file (e.g., `Russian Trusted Root CA.cer`)
- **macOS/Linux**: Downloaded as `.crt` file (e.g., `Russian_Trusted_Root_CA.crt`)

Example paths:
```bash
# Windows
set GIGACHAT_CA_BUNDLE_FILE=C:\path\to\Russian_Trusted_Root_CA.cer

# macOS/Linux
export GIGACHAT_CA_BUNDLE_FILE="/path/to/Russian_Trusted_Root_CA.crt"
```

### Development-only: Disable TLS verification (not recommended)

- Environment variable: `GIGACHAT_VERIFY_SSL_CERTS=false`
- Or pass `verify_ssl_certs=False` to `GigaChat(...)`

```python
from gigachat import GigaChat

client = GigaChat(verify_ssl_certs=False)
```

> ⚠️ **Warning:** Disabling certificate verification reduces security and is not recommended for production environments.

## Error Handling

The library raises specific exceptions for different error conditions:

```python
from gigachat import GigaChat
from gigachat.exceptions import (
    GigaChatException,
    AuthenticationError,
    RateLimitError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    RequestEntityTooLargeError,
    ServerError,
)

try:
    with GigaChat() as client:
        response = client.chat("Hello!")
        print(response.choices[0].message.content)
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except BadRequestError as e:
    print(f"Invalid request: {e}")
except ForbiddenError as e:
    print(f"Access denied: {e}")
except NotFoundError as e:
    print(f"Resource not found: {e}")
except RequestEntityTooLargeError as e:
    print(f"Request payload too large: {e}")
except ServerError as e:
    print(f"Server error: {e}")
except GigaChatException as e:
    print(f"GigaChat error: {e}")
```

### Exception Reference

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `GigaChatException` | — | Base exception for all library errors |
| `ResponseError` | — | Base exception for HTTP response errors |
| `AuthenticationError` | 401 | Invalid or expired credentials |
| `BadRequestError` | 400 | Malformed request or invalid parameters |
| `ForbiddenError` | 403 | Access denied (insufficient permissions) |
| `NotFoundError` | 404 | Requested resource not found |
| `RequestEntityTooLargeError` | 413 | Request payload too large |
| `RateLimitError` | 429 | Too many requests (use `e.retry_after`) |
| `ServerError` | 5xx | Server-side error |

## Advanced Features

### Context Variables

Track requests with custom headers for logging and debugging:

```python
from gigachat import GigaChat, session_id_cvar, request_id_cvar, custom_headers_cvar
import uuid

# Set session and request identifiers
session_id_cvar.set("user-session-12345")
request_id_cvar.set(str(uuid.uuid4()))

# Or add custom headers
custom_headers_cvar.set({"X-Custom-Header": "custom-value"})

with GigaChat() as client:
    response = client.chat("Hello!")
```

Available context variables:

| Variable | Header | Description |
|----------|--------|-------------|
| `session_id_cvar` | `X-Session-ID` | Session identifier for grouping requests |
| `request_id_cvar` | `X-Request-ID` | Unique request identifier |
| `client_id_cvar` | `X-Client-ID` | Client identifier |
| `custom_headers_cvar` | (various) | Dictionary of additional headers |

**Header precedence (when multiple sources set the same header):**

- **Explicit `access_token`** passed by the SDK (or your code) sets `Authorization: Bearer ...` first.
- **`authorization_cvar`** overrides that `Authorization` header if it is set.
- **`custom_headers_cvar`** is applied last and overrides both (including `Authorization`), as well as any other header.

### Retry Configuration

Configure automatic retry with exponential backoff for transient errors:

```python
from gigachat import GigaChat

client = GigaChat(
    max_retries=3,                          # Retry up to 3 times
    retry_backoff_factor=0.5,               # Delays: 0.5s, 1s, 2s
    retry_on_status_codes=(429, 500, 502, 503, 504),
)
```

> **Avoid “double retry” (important):**
> If you use `gigachat` through a higher-level library that also retries (for example, `langchain-gigachat` / LangChain),
> enable retries in **only one** layer. Otherwise, the effective number of attempts multiplies (e.g., 3 SDK retries × 3 framework retries).
>
> Recommended defaults:
> - Keep `gigachat` retries **disabled** (default `max_retries=0`) when the outer framework retries.
> - Or disable retries in the outer framework and configure retries here (recommended if you want one consistent retry policy).

### Deprecations

- **`Messages.data_for_context`**: deprecated by the upstream API. Do not use it in new code.
  - **Use instead**: include the relevant information directly in the message `content`, or attach files via `attachments` (file IDs) when you need to provide additional context.
  - **Timeline**: the SDK will keep accepting `data_for_context` through the `0.x` line, but it may be removed in **`1.0.0`** (or earlier if the upstream API removes it).

### Token Counting

Estimate token usage before sending requests:

```python
from gigachat import GigaChat

with GigaChat() as client:
    counts = client.tokens_count(["Hello, world!", "How are you today?"])
    for count in counts:
        print(f"Tokens: {count.tokens}, Characters: {count.characters}")
```

### Available Models

List available models and their capabilities:

```python
from gigachat import GigaChat

with GigaChat() as client:
    models = client.get_models()
    for model in models.data:
        print(f"{model.id_} (owned_by={model.owned_by})")
```

### File Operations

Upload and manage files:

```python
from gigachat import GigaChat

with GigaChat() as client:
    # Upload a file
    with open("document.pdf", "rb") as f:
        uploaded = client.upload_file(f, purpose="general")
    print(f"Uploaded: {uploaded.id}")

    # List files
    files = client.get_files()
    for file in files.data:
        print(f"{file.id}: {file.filename}")

    # Delete a file
    client.delete_file(uploaded.id)
```


### Balance Check

Check your remaining token balance (prepaid accounts only):

```python
from gigachat import GigaChat

with GigaChat(scope="GIGACHAT_API_B2B") as client:
    balance = client.get_balance()
    for entry in balance.balance:
        print(f"{entry.usage}: {entry.value}")
```

## API Reference

- [GigaChat API Documentation](https://developers.sber.ru/docs/ru/gigachat/api/main)
- [Available Models](https://developers.sber.ru/docs/ru/gigachat/models)
- [Early Access Models](https://developers.sber.ru/docs/ru/gigachat/models/preview-models)
- [Pricing](https://developers.sber.ru/docs/ru/gigachat/api/tariffs)

## Related Projects

- **[GigaChain](https://github.com/ai-forever/gigachain)** — A set of solutions for developing Russian-language LLM applications and multi-agent systems, with support for LangChain, LangGraph, LangChain4j, as well as GigaChat and other available LLMs. GigaChain covers the full development lifecycle: from prototyping and research to production deployment and ongoing support.
- **[langchain-gigachat](https://github.com/ai-forever/langchain-gigachat)** — Official LangChain integration package for GigaChat

## Versioning and stability

This project follows SemVer with additional clarity for pre-`1.0.0` releases:

- **Patch releases (`0.x.Y`)**: Backwards compatible bug fixes and internal changes.
- **Minor releases (`0.X.0`)**: May include backwards-incompatible changes. Any breaking changes must be called out in the GitHub Release notes.

### Stable release gate

To ship a release marked **Production/Stable**, the following must be true:

- **CI is green** on `main` (lint, mypy, unit tests, integration replay).
- **Local checks are green** (`make all`).
- **Packaging is sane**: sdist+wheel build and install from artifacts works (no missing files).
- **Integration cassettes are current**: re-recorded with real credentials and reviewed for scrubbing.

## Contributing

We welcome contributions of all kinds — bug reports, feature requests, documentation improvements, and code contributions!

**Quick Start:**

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/gigachat.git
cd gigachat

# Install dependencies and pre-commit hooks
make install

# Run all checks
make all
```

**For detailed contributing guidelines, please see [CONTRIBUTING.md](CONTRIBUTING.md).**

This guide covers:
- Development setup and workflow
- Code quality standards and testing
- Commit message guidelines
- Pull request process
- Issue reporting guidelines
- Project architecture

All contributions are licensed under the MIT License.

## License

This project is licensed under the MIT License.

Copyright © 2026 [GigaChain](https://github.com/ai-forever/gigachain)
