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
  - [Embeddings](#embeddings)
  - [Function Calling](#function-calling)
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

### Embeddings

Generate vector representations of text:

```python
from gigachat import GigaChat

with GigaChat() as client:
    result = client.embeddings(["Hello, world!", "Machine learning is fascinating"])

    for i, item in enumerate(result.data):
        print(f"Text {i + 1}: {len(item.embedding)} dimensions")
```

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
