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
    PrimaryChatCompletionChunk,
    PrimaryChatFunctionCall,
)
from gigachat.models import (
    ChatFunctionCall as CompatChatFunctionCall,
)
from gigachat.models import chat as chat_models
from gigachat.models.chat import (
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
    ChatFunctionCall,
    Function,
    FunctionCall,
    FunctionParameters,
    FunctionRanker,
    Messages,
    MessagesRole,
    Usage,
)
from gigachat.models.chat_completions import ChatCompletionChunk as DirectPrimaryChatCompletionChunk
from gigachat.models.chat_completions import ChatFunctionCall as DirectPrimaryChatFunctionCall

TEST_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def test_messages_role_enum() -> None:
    assert MessagesRole.USER.value == "user"
    assert MessagesRole.ASSISTANT.value == "assistant"
    assert MessagesRole.SYSTEM.value == "system"
    assert MessagesRole.FUNCTION.value == "function"
    assert MessagesRole.SEARCH_RESULT.value == "search_result"
    assert MessagesRole.FUNCTION_IN_PROGRESS.value == "function_in_progress"


def test_messages_creation() -> None:
    msg = Messages(role=MessagesRole.USER, content="hello", created=1625284800)
    assert msg.role == "user"
    assert msg.content == "hello"
    assert msg.function_call is None
    assert msg.created == 1625284800


def test_messages_function_call() -> None:
    fc = FunctionCall(name="func", arguments={"arg": "val"})
    msg = Messages(role=MessagesRole.ASSISTANT, function_call=fc)
    assert msg.function_call is not None
    assert msg.function_call.name == "func"
    assert msg.function_call.arguments == {"arg": "val"}


def test_chat_request_preserves_documented_function_call_arguments_string() -> None:
    chat = Chat(
        messages=[
            Messages(
                role=MessagesRole.ASSISTANT,
                function_call=FunctionCall(name="get_weather", arguments='{"location":"Moscow"}'),
            )
        ]
    )

    dumped = chat.model_dump(exclude_none=True)
    assert dumped["messages"][0]["function_call"]["arguments"] == '{"location":"Moscow"}'


def test_chat_request_preserves_function_call_arguments_dict() -> None:
    function_call = FunctionCall(name="get_weather", arguments={"location": "Moscow"})
    chat = Chat(messages=[Messages(role=MessagesRole.ASSISTANT, function_call=function_call)])

    dumped = chat.model_dump(exclude_none=True)

    assert function_call.arguments == {"location": "Moscow"}
    assert dumped["messages"][0]["function_call"]["arguments"] == {"location": "Moscow"}


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("temperature", 0),
        ("top_p", -0.1),
        ("top_p", 1.1),
        ("max_tokens", 0),
        ("reasoning_effort", "high"),
    ],
)
def test_chat_request_enforces_documented_generation_constraints(field_name: str, value: object) -> None:
    with pytest.raises(ValidationError):
        Chat.model_validate({"messages": [], field_name: value})


def test_chat_response_preserves_documented_function_call_arguments_string() -> None:
    completion = ChatCompletion.model_validate(
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "function_call": {"name": "get_weather", "arguments": '{"location":"Moscow"}'},
                    },
                    "index": 0,
                    "finish_reason": "function_call",
                }
            ],
            "created": 1726478395,
            "model": "GigaChat-2",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "object": "chat.completion",
        }
    )

    assert completion.choices[0].message.function_call is not None
    assert completion.choices[0].message.function_call.arguments == '{"location":"Moscow"}'


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


def test_function_parameters_preserve_json_schema_keywords() -> None:
    function = Function.model_validate(
        {
            "name": "send_sms",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "minLength": 1, "pattern": "^.+$"},
                    "contactId": {"type": "integer", "format": "int32", "minimum": 1},
                },
                "required": ["text", "contactId"],
                "additionalProperties": False,
            },
        }
    )

    dumped = function.model_dump(by_alias=True, exclude_none=True)
    assert dumped["parameters"]["properties"]["text"]["minLength"] == 1
    assert dumped["parameters"]["properties"]["text"]["pattern"] == "^.+$"
    assert dumped["parameters"]["properties"]["contactId"]["format"] == "int32"
    assert dumped["parameters"]["properties"]["contactId"]["minimum"] == 1
    assert dumped["parameters"]["additionalProperties"] is False


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


def test_chat_module_exports_public_models_without_legacy_names() -> None:
    assert Chat.__name__ == "Chat"
    assert ChatCompletion.__name__ == "ChatCompletion"
    assert all(not name.startswith("Legacy") for name in chat_models.__all__)


def test_gigachat_models_exports_keep_compat_and_primary_contracts_separate() -> None:
    assert cast(object, CompatChatCompletionChunk) is cast(object, ChatCompletionChunk)
    assert cast(object, CompatChatFunctionCall) is cast(object, ChatFunctionCall)
    assert cast(object, ChatCompletionRequest) is not cast(object, Chat)
    assert cast(object, ChatCompletionResponse) is not cast(object, ChatCompletion)
    assert cast(object, PrimaryChatCompletionChunk) is cast(object, DirectPrimaryChatCompletionChunk)
    assert cast(object, PrimaryChatFunctionCall) is cast(object, DirectPrimaryChatFunctionCall)
    assert cast(object, PrimaryChatCompletionChunk) is not cast(object, CompatChatCompletionChunk)
    assert cast(object, PrimaryChatFunctionCall) is not cast(object, CompatChatFunctionCall)


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
