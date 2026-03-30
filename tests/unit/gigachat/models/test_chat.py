from typing import Any, Dict

import pytest
from pydantic import ValidationError

from gigachat.models.chat import (
    Chat,
    ChatCompletion,
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


def test_chat_top_logprobs_dump() -> None:
    chat = Chat(messages=[], top_logprobs=2)

    assert chat.model_dump(exclude_none=True)["top_logprobs"] == 2


def test_chat_unnormalized_history_dump() -> None:
    chat = Chat(messages=[], unnormalized_history=True)

    assert chat.model_dump(exclude_none=True)["unnormalized_history"] is True


def test_chat_completion_message_logprobs() -> None:
    completion = ChatCompletion.model_validate(
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Да",
                        "logprobs": [
                            {
                                "chosen": {"token": "Да", "logprob": -0.1},
                                "top": [
                                    {"token": "Да", "logprob": -0.1},
                                    {"token": "Нет", "logprob": -1.5},
                                ],
                            }
                        ],
                    },
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            "created": 1678878333,
            "model": "GigaChat:v1.2.19.2",
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
            },
            "object": "chat.completion",
        }
    )

    assert completion.choices[0].message.logprobs is not None
    assert completion.choices[0].message.logprobs[0].chosen.token == "Да"
    assert completion.choices[0].message.logprobs[0].chosen.logprob == -0.1
    assert completion.choices[0].message.logprobs[0].top[1].token == "Нет"
