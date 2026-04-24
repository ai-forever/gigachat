from typing import Any, Dict

import pytest
from pydantic import ValidationError

from gigachat.models.chat import (
    Chat,
    Function,
    FunctionCall,
    FunctionParameters,
    FunctionRanker,
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


def test_usage_validation() -> None:
    with pytest.raises(ValidationError):
        Usage(prompt_tokens="invalid", completion_tokens=10, total_tokens=20)


def test_function_parameters_default() -> None:
    params = FunctionParameters()
    assert params.type_ == "object"


def test_chat_function_ranker_from_dict() -> None:
    chat = Chat(messages=[], function_ranker={"enabled": True, "top_n": 3})

    assert isinstance(chat.function_ranker, FunctionRanker)
    assert chat.function_ranker.enabled is True
    assert chat.function_ranker.top_n == 3
    assert chat.model_dump(exclude_none=True)["function_ranker"] == {"enabled": True, "top_n": 3}


def test_chat_function_ranker_omitted_by_default() -> None:
    chat = Chat(messages=[])

    assert chat.function_ranker is None
    assert "function_ranker" not in chat.model_dump(exclude_none=True)
