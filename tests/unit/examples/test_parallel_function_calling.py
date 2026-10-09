from typing import Any, Dict, List

import pytest
from examples.tools.parallel_function_calling import build_request, validate_parallel_calls

from gigachat.models import ChatCompletionResponse


def response_with_calls(calls: List[Dict[str, Any]]) -> ChatCompletionResponse:
    return ChatCompletionResponse.model_validate(
        {
            "messages": [
                {
                    "role": "assistant",
                    "content": [{"text": "Checking now"}, *({"function_call": call} for call in calls)],
                }
            ]
        }
    )


def test_request_enables_parallel_calls_under_model_options() -> None:
    payload = build_request().model_dump(exclude_none=True, by_alias=True)
    assert payload["model_options"]["parallel_tool_calls"] is True
    assert payload["model_options"]["max_tokens"] > 0
    assert "parallel_tool_calls" not in payload


def test_zero_and_one_call_are_valid() -> None:
    assert validate_parallel_calls(response_with_calls([])) == []
    single = response_with_calls([{"name": "get_weather", "arguments": {"city": "Moscow"}}])
    assert len(validate_parallel_calls(single)) == 1


def test_same_function_can_have_two_distinct_calls() -> None:
    response = response_with_calls(
        [
            {"id": "call-1", "name": "get_weather", "arguments": {"city": "Moscow"}},
            {"id": "call-2", "name": "get_weather", "arguments": {"city": "Kazan"}},
        ]
    )
    assert [call.id_ for call in validate_parallel_calls(response)] == ["call-1", "call-2"]


@pytest.mark.parametrize("second_id", [None, "", "call-1"])
def test_multiple_calls_require_unique_nonempty_ids(second_id: Any) -> None:
    response = response_with_calls(
        [
            {"id": "call-1", "name": "get_weather", "arguments": {}},
            {"id": second_id, "name": "get_weather", "arguments": {}},
        ]
    )
    with pytest.raises(RuntimeError, match="distinct, nonempty IDs"):
        validate_parallel_calls(response)
