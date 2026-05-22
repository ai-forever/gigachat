import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, cast

import pytest
from pydantic import ValidationError

from gigachat.models import (
    ChatCompletionChunk as CompatChatCompletionChunk,
)
from gigachat.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from gigachat.models import chat as chat_models
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
from gigachat.models.chat_completions import ChatCompletionChunk as PrimaryChatCompletionChunk

TEST_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


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


def test_chat_module_exports_public_models_without_legacy_names() -> None:
    assert Chat.__name__ == "Chat"
    assert ChatCompletion.__name__ == "ChatCompletion"
    assert all(not name.startswith("Legacy") for name in chat_models.__all__)


def test_gigachat_models_exports_keep_compat_and_primary_contracts_separate() -> None:
    assert cast(object, CompatChatCompletionChunk) is cast(object, ChatCompletionChunk)
    assert cast(object, ChatCompletionRequest) is not cast(object, Chat)
    assert cast(object, ChatCompletionResponse) is not cast(object, ChatCompletion)
    assert cast(object, PrimaryChatCompletionChunk) is not cast(object, CompatChatCompletionChunk)


def test_chat_request_round_trip_unchanged() -> None:
    payload = json.loads((TEST_DATA_DIR / "chat.json").read_text(encoding="utf-8"))
    expected_payload = deepcopy(payload)
    expected_payload["messages"][0].pop("reasoning_effort")

    compat_model = Chat.model_validate(payload)

    assert compat_model.model_dump(exclude_none=True, by_alias=True) == expected_payload


def test_chat_completion_response_round_trip_unchanged() -> None:
    payload = json.loads((TEST_DATA_DIR / "chat_completion.json").read_text(encoding="utf-8"))

    compat_model = ChatCompletion.model_validate(payload)

    assert compat_model.model_dump(exclude_none=True, by_alias=True) == payload


def test_primary_response_contract_does_not_validate_as_chat_completion() -> None:
    payload = {
        "model": "GigaChat-2-Max",
        "created_at": 1760434636,
        "messages": [{"role": "assistant", "content": "primary response"}],
    }

    response = ChatCompletionResponse.model_validate(payload)

    assert response.messages is not None
    with pytest.raises(ValidationError):
        ChatCompletion.model_validate(payload)
