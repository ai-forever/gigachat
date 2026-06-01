"""Integration tests for /v2/chat/completions endpoint using VCR cassettes."""

import os
import re
from typing import Any, Dict, List, Tuple

import pytest
from pydantic import BaseModel, Field

from gigachat import GigaChat
from gigachat.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatFunctionSpecification,
    ChatMessage,
    ChatModelOptions,
    ChatResponseFormat,
    ChatTool,
    ChatToolConfig,
    ChatWebSearchTool,
)
from gigachat.models.chat_completions import ChatCompletionChunk


class StructuredAnswer(BaseModel):
    """Structured answer returned by response_format=json_schema."""

    answer: str
    n: int = Field(ge=0, le=10)


PRIMARY_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat")


ORDER_STATUS_FUNCTION = {
    "name": "get_order_status",
    "description": "Get delivery status for an order.",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "Order identifier."},
        },
        "required": ["order_id"],
    },
    "return_parameters": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "status": {"type": "string"},
            "eta": {"type": "string"},
        },
        "required": ["order_id", "status", "eta"],
    },
}


def _first_message(result: ChatCompletionResponse) -> ChatMessage:
    """Return the first response message."""
    assert result.messages
    return result.messages[0]


def _extract_assistant_text(result: ChatCompletionResponse) -> str:
    """Return the first non-empty assistant text content."""
    for message in result.messages:
        if message.role != "assistant" or not message.content:
            continue

        text = "".join(part.text or "" for part in message.content)
        if text:
            return text

    raise AssertionError("Response has no assistant text content")


def _message_sources(message: ChatMessage) -> List[Tuple[str, str]]:
    """Return unique sources from message inline data."""
    sources: List[Tuple[str, str]] = []
    seen = set()
    for part in message.content or []:
        if part.inline_data is None or part.inline_data.sources is None:
            continue

        for source in part.inline_data.sources.values():
            key = (source.title or "Untitled source", source.url or "")
            if key in seen:
                continue
            seen.add(key)
            sources.append(key)
    return sources


def _message_file_ids(message: ChatMessage) -> List[str]:
    """Return file IDs from message content."""
    file_ids: List[str] = []
    for part in message.content or []:
        file_ids.extend(file_.id_ for file_ in part.files or [])
    return file_ids


def _extract_function_call(response: ChatCompletionResponse) -> Dict[str, Any]:
    """Return the first function call from a response."""
    for message in response.messages:
        function_call = message.function_call
        if function_call is None:
            for part in message.content or []:
                if part.function_call is not None:
                    function_call = part.function_call
                    break

        if function_call is None:
            continue

        return {
            "name": function_call.name,
            "arguments": function_call.arguments or {},
            "state_id": message.tools_state_id,
            "assistant_message": message.model_dump(mode="json", exclude_none=True, by_alias=True),
        }

    raise AssertionError("The model did not call a function")


@pytest.mark.integration
@pytest.mark.vcr
def test_primary_chat_create_simple(gigachat_client: GigaChat) -> None:
    """Test basic primary chat completion."""
    payload = ChatCompletionRequest(
        model=PRIMARY_MODEL,
        messages=[ChatMessage(role="user", content="Say 'Hello' and nothing else")],
    )

    result = gigachat_client.chat.create(payload)

    assert isinstance(result, ChatCompletionResponse)
    assert result.messages
    assert _extract_assistant_text(result)
    if result.usage is not None and result.usage.total_tokens is not None:
        assert result.usage.total_tokens > 0


@pytest.mark.integration
@pytest.mark.vcr
async def test_primary_achat_create_simple(gigachat_async_client: GigaChat) -> None:
    """Test basic primary chat completion asynchronously."""
    payload = ChatCompletionRequest(
        model=PRIMARY_MODEL,
        messages=[ChatMessage(role="user", content="Say 'Hello' and nothing else")],
    )

    result = await gigachat_async_client.achat.create(payload)

    assert isinstance(result, ChatCompletionResponse)
    assert result.messages
    assert _extract_assistant_text(result)
    if result.usage is not None and result.usage.total_tokens is not None:
        assert result.usage.total_tokens > 0


@pytest.mark.integration
@pytest.mark.vcr
def test_primary_chat_parse_json_schema(gigachat_client: GigaChat) -> None:
    """Test primary chat.parse() parses JSON into a Pydantic model."""
    payload = ChatCompletionRequest(
        model=PRIMARY_MODEL,
        messages=[
            ChatMessage(role="user", content='Return {"answer":"ok","n":3} exactly.'),
        ],
    )

    completion, parsed = gigachat_client.chat.parse(payload, response_format=StructuredAnswer, strict=True)

    assert isinstance(completion, ChatCompletionResponse)
    assert parsed.model_dump() == {"answer": "ok", "n": 3}


@pytest.mark.integration
@pytest.mark.vcr
async def test_primary_achat_parse_json_schema(gigachat_async_client: GigaChat) -> None:
    """Test primary achat.parse() parses JSON into a Pydantic model."""
    payload = ChatCompletionRequest(
        model=PRIMARY_MODEL,
        messages=[
            ChatMessage(role="user", content='Return {"answer":"ok","n":3} exactly.'),
        ],
    )

    completion, parsed = await gigachat_async_client.achat.parse(
        payload,
        response_format=StructuredAnswer,
        strict=True,
    )

    assert isinstance(completion, ChatCompletionResponse)
    assert parsed.model_dump() == {"answer": "ok", "n": 3}


@pytest.mark.integration
@pytest.mark.vcr
def test_primary_chat_stream_simple(gigachat_client: GigaChat) -> None:
    """Test primary streaming chat completion."""
    payload = ChatCompletionRequest(
        model=PRIMARY_MODEL,
        messages=[ChatMessage(role="user", content="Count from 1 to 3")],
    )

    chunks = list(gigachat_client.chat.stream(payload))

    assert chunks
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in chunks)
    assert any(chunk.messages for chunk in chunks)
    assert any(chunk.finish_reason is not None for chunk in chunks)


@pytest.mark.integration
@pytest.mark.vcr
def test_primary_chat_regex_format(gigachat_client: GigaChat) -> None:
    """Test regex response format on the primary chat contract."""
    payload = ChatCompletionRequest(
        model=PRIMARY_MODEL,
        messages=[ChatMessage(role="user", content="Generate one support ticket code.")],
        model_options=ChatModelOptions(
            response_format=ChatResponseFormat(type="regex", regex=r"[A-Z]{3}-\d{4}"),
        ),
    )

    result = gigachat_client.chat.create(payload)

    assert re.fullmatch(r"[A-Z]{3}-\d{4}", _extract_assistant_text(result))


@pytest.mark.integration
@pytest.mark.vcr
def test_primary_chat_function_tool_roundtrip(gigachat_client: GigaChat) -> None:
    """Test a client-defined function tool roundtrip."""
    request = ChatCompletionRequest(
        model=PRIMARY_MODEL,
        messages=[ChatMessage(role="user", content="Check order A-1024 and answer naturally.")],
        tools=[ChatTool(functions={"specifications": [ChatFunctionSpecification(**ORDER_STATUS_FUNCTION)]})],
        tool_config=ChatToolConfig(mode="forced", function_name="get_order_status"),
    )

    first_response = gigachat_client.chat.create(request)
    call = _extract_function_call(first_response)

    assert call["name"] == "get_order_status"
    assert call["arguments"] == {"order_id": "A-1024"}
    assert isinstance(call["state_id"], str)
    assert call["state_id"]

    request_data = request.model_dump(mode="json", exclude_none=True, by_alias=True)
    request_data.pop("tool_config", None)
    final_payload = {
        **request_data,
        "messages": request_data["messages"]
        + [
            call["assistant_message"],
            {
                "role": "tool",
                "content": [
                    {
                        "function_result": {
                            "name": call["name"],
                            "result": {
                                "order_id": "A-1024",
                                "status": "packed",
                                "eta": "tomorrow",
                            },
                        }
                    }
                ],
                "tools_state_id": call["state_id"],
            },
        ],
    }

    final_response = gigachat_client.chat.create(final_payload)

    assert "packed" in _extract_assistant_text(final_response)


@pytest.mark.integration
@pytest.mark.vcr
def test_primary_chat_builtin_tools(gigachat_client: GigaChat) -> None:
    """Test representative built-in tools from examples/tools."""
    web_search = gigachat_client.chat.create(
        ChatCompletionRequest(
            model=PRIMARY_MODEL,
            messages=[ChatMessage(role="user", content="What is new in the latest stable Python release?")],
            tools=[ChatTool(web_search=ChatWebSearchTool(type="actual_info_web_search"))],
            tool_config=ChatToolConfig(mode="forced", tool_name="web_search"),
        )
    )
    assert _extract_assistant_text(web_search)
    assert _message_sources(_first_message(web_search))

    code_interpreter = gigachat_client.chat.create(
        {
            "model": PRIMARY_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": "Calculate the sum of the first 20 prime numbers. Use code."}],
                }
            ],
            "tools": ["code_interpreter"],
            "tool_config": {"mode": "auto"},
        }
    )
    assert "639" in _extract_assistant_text(code_interpreter)

    url_content_extraction = gigachat_client.chat.create(
        ChatCompletionRequest(
            model=PRIMARY_MODEL,
            messages=[
                ChatMessage(
                    role="user",
                    content="Read https://docs.python.org/3/library/pathlib.html and list three use cases for pathlib.",
                )
            ],
            tools=[ChatTool(url_content_extraction={})],
            tool_config=ChatToolConfig(mode="forced", tool_name="url_content_extraction"),
        )
    )
    assert "pathlib" in _extract_assistant_text(url_content_extraction)

    image_generation = gigachat_client.chat.create(
        ChatCompletionRequest(
            model=PRIMARY_MODEL,
            messages=[
                ChatMessage(role="user", content="Create a simple square icon concept for a Python SDK release.")
            ],
            tools=[ChatTool(image_generate={})],
            tool_config=ChatToolConfig(mode="forced", tool_name="image_generate"),
        )
    )
    image_message = _first_message(image_generation)
    assert image_message.content
    assert any(part.text or part.files for part in image_message.content)


@pytest.mark.integration
@pytest.mark.vcr
async def test_primary_achat_stream_simple(gigachat_async_client: GigaChat) -> None:
    """Test primary streaming chat completion asynchronously."""
    payload = ChatCompletionRequest(
        model=PRIMARY_MODEL,
        messages=[ChatMessage(role="user", content="Count from 1 to 3")],
    )

    chunks = [chunk async for chunk in gigachat_async_client.achat.stream(payload)]

    assert chunks
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in chunks)
    assert any(chunk.messages for chunk in chunks)
    assert any(chunk.finish_reason is not None for chunk in chunks)
