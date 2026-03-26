from local.v2.function_call_v2_example import build_followup_chat, build_initial_chat, extract_function_call

from gigachat.models.chat_v2 import ChatCompletionV2


def test_build_followup_chat_keeps_assistant_function_call_before_tool_result() -> None:
    initial_chat = build_initial_chat()
    first_response = ChatCompletionV2.model_validate(
        {
            "model": "GigaChat-2-Max",
            "created_at": 1710000000,
            "messages": [
                {
                    "role": "assistant",
                    "tools_state_id": "tool-state-1",
                    "content": [
                        {
                            "function_call": {
                                "name": "weather-get_current_weather",
                                "arguments": {
                                    "location": "Moscow",
                                },
                            }
                        }
                    ],
                }
            ],
        }
    )
    first_response_dump = first_response.model_dump(mode="json", exclude_none=True)
    function_call = extract_function_call("raw-response", first_response)

    followup_chat = build_followup_chat(
        initial_chat=initial_chat,
        assistant_messages=first_response_dump["messages"],
        function_call=function_call,
        function_result={"status": "success", "temperature": 18},
    )

    assert followup_chat.tool_config is not None
    assert followup_chat.tool_config.mode == "none"
    assert len(followup_chat.messages) == 4
    assert followup_chat.messages[2].role == "assistant"
    assert followup_chat.messages[2].content[0].function_call is not None
    assert followup_chat.messages[2].content[0].function_call.name == "weather-get_current_weather"
    assert followup_chat.messages[3].role == "tool"
    assert followup_chat.messages[3].tools_state_id == "tool-state-1"
    assert followup_chat.messages[3].content[0].function_result is not None
    assert followup_chat.messages[3].content[0].function_result.name == "weather-get_current_weather"
