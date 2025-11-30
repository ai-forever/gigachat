from typing import Any, Dict

import pytest
from pydantic import ValidationError

from gigachat.models.chat import (
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
    Function,
    FunctionCall,
    FunctionParameters,
    Messages,
    MessagesRole,
    Usage,
)


def test_messages_role_enum() -> None:
    assert MessagesRole.USER.value == "user"
    assert MessagesRole.ASSISTANT.value == "assistant"
    assert MessagesRole.SYSTEM.value == "system"
    assert MessagesRole.FUNCTION.value == "function"
    assert MessagesRole.SEARCH_RESULT.value == "search_result"
    assert MessagesRole.FUNCTION_IN_PROGRESS.value == "function_in_progress"


def test_messages_creation() -> None:
    msg = Messages(role=MessagesRole.USER, content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"
    assert msg.function_call is None


def test_messages_function_call() -> None:
    fc = FunctionCall(name="func", arguments={"arg": "val"})
    msg = Messages(role=MessagesRole.ASSISTANT, function_call=fc)
    assert msg.function_call is not None
    assert msg.function_call.name == "func"
    assert msg.function_call.arguments == {"arg": "val"}


def test_function_model_validator() -> None:
    # Test title -> name alias
    data: Dict[str, Any] = {
        "title": "my_func",
        "description": "desc",
        "parameters": {"type": "object"},
    }
    func = Function.model_validate(data)
    assert func.name == "my_func"
    assert func.description == "desc"

    # Test properties -> parameters adapter
    data = {
        "name": "my_func",
        "properties": {"prop": {"type": "string"}},
    }
    func = Function.model_validate(data)
    assert func.parameters is not None
    assert func.parameters.properties is not None
    assert "prop" in func.parameters.properties


def test_chat_creation() -> None:
    chat = Chat(
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        model="GigaChat",
        temperature=0.5,
    )
    assert chat.model == "GigaChat"
    assert len(chat.messages) == 1
    assert chat.temperature == 0.5


def test_chat_completion_creation() -> None:
    data = {
        "choices": [
            {
                "message": {"role": "assistant", "content": "response"},
                "index": 0,
                "finish_reason": "stop",
            }
        ],
        "created": 1234567890,
        "model": "GigaChat",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        "object": "chat.completion",
    }
    completion = ChatCompletion.model_validate(data)
    assert completion.model == "GigaChat"
    assert completion.created == 1234567890
    assert completion.object_ == "chat.completion"
    assert len(completion.choices) == 1
    assert completion.choices[0].message.content == "response"
    assert completion.usage.total_tokens == 30


def test_chat_completion_chunk_creation() -> None:
    data = {
        "choices": [
            {
                "delta": {"content": "chunk"},
                "index": 0,
                "finish_reason": None,
            }
        ],
        "created": 1234567890,
        "model": "GigaChat",
        "object": "chat.completion.chunk",
    }
    chunk = ChatCompletionChunk.model_validate(data)
    assert chunk.object_ == "chat.completion.chunk"
    assert chunk.choices[0].delta.content == "chunk"


def test_usage_validation() -> None:
    with pytest.raises(ValidationError):
        Usage(prompt_tokens="invalid", completion_tokens=10, total_tokens=20)


def test_function_parameters_default() -> None:
    params = FunctionParameters()
    assert params.type_ == "object"
