from typing import Any, Dict

from examples.tools.function_calling import add_function_result, extract_call

from gigachat.models import ChatCompletionResponse


class Response:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self.payload = payload

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return self.payload


def test_extract_call_reads_function_call_from_content_part() -> None:
    response = Response(
        {
            "messages": [
                {
                    "role": "assistant",
                    "tool_state_id": "tool-state-1",
                    "content": [
                        {
                            "function_call": {
                                "name": "get_weather",
                                "arguments": {"location": "Moscow"},
                            }
                        }
                    ],
                    "finish_reason": "function_call",
                }
            ]
        }
    )

    call = extract_call(response)

    assert call["name"] == "get_weather"
    assert call["arguments"] == {"location": "Moscow"}
    assert call["state_field"] == "tools_state_id"
    assert call["state_id"] == "tool-state-1"
    assert call["assistant_message"]["tools_state_id"] == "tool-state-1"
    assert "tool_state_id" not in call["assistant_message"]


def test_add_function_result_preserves_state_field_name() -> None:
    request = {
        "messages": [
            {
                "role": "user",
                "content": [{"text": "What is the weather in Moscow?"}],
            }
        ]
    }
    call = {
        "name": "get_weather",
        "state_field": "tools_state_id",
        "state_id": "tool-state-1",
        "assistant_message": {"role": "assistant", "tools_state_id": "tool-state-1"},
    }

    payload = add_function_result(request, call, {"temperature": 18})

    assert payload["messages"][2]["tools_state_id"] == "tool-state-1"
    assert "tool_config" not in payload


def test_single_function_example_preserves_wire_id() -> None:
    response = ChatCompletionResponse.model_validate(
        {
            "messages": [
                {
                    "role": "assistant",
                    "tools_state_id": "state-1",
                    "content": [
                        {
                            "function_call": {
                                "id": "call-1",
                                "name": "get_weather",
                                "arguments": {"location": "Moscow"},
                            }
                        }
                    ],
                }
            ]
        }
    )
    call = extract_call(response)
    payload = add_function_result({"messages": []}, call, {"temperature": 18})
    assert payload["messages"][0]["content"][0]["function_call"]["id"] == "call-1"
    assert payload["messages"][1]["content"][0]["function_result"]["id"] == "call-1"
