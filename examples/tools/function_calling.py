"""Use function calling with models or plain dictionaries."""

import json
from typing import Any, Dict

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatFunctionSpecification, ChatMessage, ChatTool, ChatToolConfig


def get_weather(location: str) -> Dict[str, Any]:
    """Return mock weather data for a city."""
    return {
        "location": location,
        "temperature": 18,
        "unit": "celsius",
        "conditions": "cloudy",
    }


WEATHER_FUNCTION = {
    "name": "get_weather",
    "description": "Get current weather for a city.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name.",
            }
        },
        "required": ["location"],
    },
}


def request_with_models() -> ChatCompletionRequest:
    """Build a function-calling request with SDK models."""
    return ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="What is the weather in Moscow? Answer in one sentence.",
            )
        ],
        tools=[
            ChatTool(
                functions={
                    "specifications": [ChatFunctionSpecification(**WEATHER_FUNCTION)],
                }
            )
        ],
        tool_config=ChatToolConfig(mode="auto"),
    )


def request_with_dict() -> Dict[str, Any]:
    """Build a function-calling request with a plain dict."""
    return {
        "messages": [
            {
                "role": "user",
                "content": [{"text": "What is the weather in Moscow? Answer in one sentence."}],
            }
        ],
        "tools": [
            {
                "functions": {
                    "specifications": [WEATHER_FUNCTION],
                }
            }
        ],
        "tool_config": {"mode": "auto"},
    }


def extract_call(response: Any) -> Dict[str, Any]:
    """Return the first function call from a response."""
    response_data = response.model_dump(mode="json", exclude_none=True)
    for message in response_data["messages"]:
        function_call = message.get("function_call")
        if function_call is None:
            for part in message.get("content") or []:
                if isinstance(part, dict) and part.get("function_call") is not None:
                    function_call = part["function_call"]
                    break

        if function_call is not None:
            state_field = next(
                (
                    field
                    for field in ("tools_state_id", "tool_state_id", "functions_state_id")
                    if message.get(field) is not None
                ),
                None,
            )
            state_id = message.get(state_field) if state_field is not None else None
            assistant_message = dict(message)
            assistant_message.pop("tool_state_id", None)
            assistant_message.pop("functions_state_id", None)
            if state_id is not None:
                assistant_message["tools_state_id"] = state_id
            return {
                "name": function_call["name"],
                "arguments": function_call.get("arguments") or {},
                "state_field": "tools_state_id" if state_id is not None else None,
                "state_id": state_id,
                "assistant_message": assistant_message,
            }

    raise RuntimeError("The model did not call a function.")


def add_function_result(request: Any, call: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """Append the function result to the conversation."""
    payload = (
        request.model_dump(mode="json", exclude_none=True, by_alias=True) if hasattr(request, "model_dump") else request
    )
    payload = dict(payload)
    payload.pop("tool_config", None)
    tool_message = {
        "role": "tool",
        "content": [
            {
                "function_result": {
                    "name": call["name"],
                    "result": result,
                }
            }
        ],
    }

    if call["state_field"] is not None:
        tool_message[call["state_field"]] = call["state_id"]

    return {
        **payload,
        "messages": payload["messages"] + [call["assistant_message"], tool_message],
    }


def run(client: GigaChat, request: Any) -> str:
    """Run one function-calling roundtrip."""
    first_response = client.chat.create(request)
    call = extract_call(first_response)

    if call["name"] != "get_weather":
        raise RuntimeError(f"Unexpected function call: {call['name']}")

    result = get_weather(**call["arguments"])
    final_response = client.chat.create(add_function_result(request, call, result))
    return json.dumps(final_response.model_dump(mode="json", exclude_none=True), ensure_ascii=False, indent=2)


def main() -> None:
    """Run both request styles."""
    load_dotenv()

    with GigaChat() as client:
        for title, request in (
            ("Models", request_with_models()),
            ("Dict", request_with_dict()),
        ):
            print(f"\n{title}:")
            print(run(client, request))


if __name__ == "__main__":
    main()
