"""Integration tests for /chat/completions endpoint using VCR cassettes."""

import json

import pytest
from pydantic import BaseModel, Field

from gigachat import GigaChat
from gigachat.exceptions import NotFoundError
from gigachat.models import Chat, ChatCompletion, ChatCompletionChunk, Messages, MessagesRole

_NO_MARKDOWN_NO_FENCES_SYSTEM = (
    "You are a JSON API. Output must be a single JSON object and NOTHING else. "
    "Do not use markdown. Do not wrap in ``` code fences. Do not add comments. "
    "Do not add trailing text."
)


@pytest.mark.integration
@pytest.mark.vcr
def test_chat_simple(gigachat_client: GigaChat) -> None:
    """Test basic chat completion with a single user message."""
    payload = Chat(messages=[Messages(role=MessagesRole.USER, content="Say 'Hello' and nothing else")])
    result = gigachat_client.chat(payload)

    assert isinstance(result, ChatCompletion)
    assert result.object_ == "chat.completion"
    assert len(result.choices) > 0
    assert result.choices[0].message.role == "assistant"
    assert result.choices[0].message.content
    assert result.usage.total_tokens > 0


@pytest.mark.integration
@pytest.mark.vcr
def test_chat_response_format_json_schema(gigachat_client: GigaChat) -> None:
    """Test response_format=json_schema returns JSON (as a string) in message.content."""
    payload = Chat(
        messages=[
            Messages(role=MessagesRole.SYSTEM, content=_NO_MARKDOWN_NO_FENCES_SYSTEM),
            Messages(
                role=MessagesRole.USER,
                content='Return {"answer":"ok","n":3} exactly.',
            ),
        ],
        response_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "n": {"type": "integer"},
                },
                "required": ["answer", "n"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    )

    result = gigachat_client.chat(payload)

    assert isinstance(result, ChatCompletion)
    content = result.choices[0].message.content
    data = json.loads(content)
    assert data == {"answer": "ok", "n": 3}


@pytest.mark.integration
@pytest.mark.vcr
async def test_achat_simple(gigachat_async_client: GigaChat) -> None:
    """Test basic chat completion asynchronously."""
    payload = Chat(messages=[Messages(role=MessagesRole.USER, content="Say 'Hello' and nothing else")])
    result = await gigachat_async_client.achat(payload)

    assert isinstance(result, ChatCompletion)
    assert result.object_ == "chat.completion"
    assert len(result.choices) > 0
    assert result.choices[0].message.role == "assistant"
    assert result.choices[0].message.content
    assert result.usage.total_tokens > 0


@pytest.mark.integration
@pytest.mark.vcr
async def test_achat_response_format_json_schema(gigachat_async_client: GigaChat) -> None:
    """Test async response_format=json_schema returns JSON in message.content."""
    payload = Chat(
        messages=[
            Messages(role=MessagesRole.SYSTEM, content=_NO_MARKDOWN_NO_FENCES_SYSTEM),
            Messages(
                role=MessagesRole.USER,
                content='Return {"answer":"ok","n":3} exactly.',
            ),
        ],
        response_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "n": {"type": "integer"},
                },
                "required": ["answer", "n"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    )

    result = await gigachat_async_client.achat(payload)

    assert isinstance(result, ChatCompletion)
    content = result.choices[0].message.content
    data = json.loads(content)
    assert data == {"answer": "ok", "n": 3}


@pytest.mark.integration
@pytest.mark.vcr
def test_chat_parse_json_schema(gigachat_client: GigaChat) -> None:
    """Test chat_parse() sets response_format and parses JSON into a Pydantic model."""

    class Out(BaseModel):
        answer: str
        n: int = Field(ge=0, le=10)

    payload = Chat(
        messages=[
            Messages(role=MessagesRole.SYSTEM, content=_NO_MARKDOWN_NO_FENCES_SYSTEM),
            Messages(role=MessagesRole.USER, content='Return {"answer":"ok","n":3} exactly.'),
        ]
    )

    completion, parsed = gigachat_client.chat_parse(payload, response_model=Out, strict=True)
    assert isinstance(completion, ChatCompletion)
    assert parsed.model_dump() == {"answer": "ok", "n": 3}


@pytest.mark.integration
@pytest.mark.vcr
async def test_achat_parse_json_schema(gigachat_async_client: GigaChat) -> None:
    """Test achat_parse() sets response_format and parses JSON into a Pydantic model."""

    class Out(BaseModel):
        answer: str
        n: int = Field(ge=0, le=10)

    payload = Chat(
        messages=[
            Messages(role=MessagesRole.SYSTEM, content=_NO_MARKDOWN_NO_FENCES_SYSTEM),
            Messages(role=MessagesRole.USER, content='Return {"answer":"ok","n":3} exactly.'),
        ]
    )

    completion, parsed = await gigachat_async_client.achat_parse(payload, response_model=Out, strict=True)
    assert isinstance(completion, ChatCompletion)
    assert parsed.model_dump() == {"answer": "ok", "n": 3}


@pytest.mark.integration
@pytest.mark.vcr
def test_stream_simple(gigachat_client: GigaChat) -> None:
    """Test streaming chat completion."""
    payload = Chat(messages=[Messages(role=MessagesRole.USER, content="Count from 1 to 3")])
    chunks = list(gigachat_client.stream(payload))

    assert len(chunks) > 0
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in chunks)
    assert chunks[-1].choices[0].finish_reason is not None


@pytest.mark.integration
@pytest.mark.vcr
async def test_astream_simple(gigachat_async_client: GigaChat) -> None:
    """Test streaming chat completion asynchronously."""
    payload = Chat(messages=[Messages(role=MessagesRole.USER, content="Count from 1 to 3")])
    chunks = [chunk async for chunk in gigachat_async_client.astream(payload)]

    assert len(chunks) > 0
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in chunks)
    assert chunks[-1].choices[0].finish_reason is not None


@pytest.mark.integration
@pytest.mark.vcr
def test_chat_model_not_found(gigachat_client: GigaChat) -> None:
    """Test 404 error when using non-existent model."""
    payload = Chat(model="NonExistentModel", messages=[Messages(role=MessagesRole.USER, content="Hello")])
    with pytest.raises(NotFoundError) as exc_info:
        gigachat_client.chat(payload)

    assert exc_info.value.status_code == 404


@pytest.mark.integration
@pytest.mark.vcr
async def test_achat_model_not_found(gigachat_async_client: GigaChat) -> None:
    """Test 404 error when using non-existent model asynchronously."""
    payload = Chat(model="NonExistentModel", messages=[Messages(role=MessagesRole.USER, content="Hello")])
    with pytest.raises(NotFoundError) as exc_info:
        await gigachat_async_client.achat(payload)

    assert exc_info.value.status_code == 404
