"""Run parallel local functions and return correlated results until the final answer."""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from examples.tools.parallel_function_calling import build_request, validate_parallel_calls
from gigachat import GigaChat
from gigachat.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatContentPart,
    ChatFunctionResult,
    ChatMessage,
)
from gigachat.models.chat_completions import ChatFunctionCall


def execute_function(call: ChatFunctionCall) -> Dict[str, Any]:
    """Return demonstration data, not live weather or exchange rates."""
    if not isinstance(call.arguments, dict):
        raise ValueError("Function arguments must be an object")
    if call.name == "get_weather":
        city = call.arguments.get("city")
        if not isinstance(city, str):
            raise ValueError("city must be a string")
        return {"city": city, "temperature_c": 12 if city == "Moscow" else 8, "demo": True}
    if call.name == "get_rate":
        currency = call.arguments.get("currency")
        if not isinstance(currency, str):
            raise ValueError("currency must be a string")
        return {"currency": currency, "rubles": 90.5, "demo": True}
    raise ValueError(f"Unknown function: {call.name}")


def build_follow_up_request(request: ChatCompletionRequest, response: ChatCompletionResponse) -> ChatCompletionRequest:
    """Preserve all response messages and correlate each tool result by ID."""
    validate_parallel_calls(response)
    messages = list(request.messages) + response.messages
    with ThreadPoolExecutor(max_workers=4) as pool:
        batches = []
        for message in response.messages:
            if message.role != "assistant":
                continue
            calls = [part.function_call for part in message.content or [] if part.function_call is not None]
            if calls:
                batches.append((message, calls, [pool.submit(execute_function, call) for call in calls]))
        for message, calls, futures in batches:
            results = [
                ChatContentPart(
                    function_result=ChatFunctionResult(id_=call.id_, name=call.name, result=future.result())
                )
                for call, future in zip(calls, futures)
            ]
            messages.append(ChatMessage(role="tool", tools_state_id=message.tools_state_id, content=results))
    payload = request.model_dump(mode="json", by_alias=True, exclude_none=True)
    payload["messages"] = [message.model_dump(mode="json", by_alias=True, exclude_none=True) for message in messages]
    # Any/forced selection is only needed initially; allow a final text answer.
    payload.pop("tool_config", None)
    return ChatCompletionRequest.model_validate(payload)


def extract_final_text(response: ChatCompletionResponse) -> str:
    """Read assistant text while excluding reasoning and partial tool rounds."""
    if validate_parallel_calls(response):
        raise RuntimeError("The model requested another tool round")
    text = "".join(
        part.text or ""
        for message in response.messages
        if message.role == "assistant"
        for part in message.content or []
    ).strip()
    if not text:
        raise RuntimeError("The response does not contain a final assistant answer")
    return text


def run(client: GigaChat, request: Optional[ChatCompletionRequest] = None, max_steps: int = 8) -> str:
    """Run a bounded tool loop; parallel calls are permitted, not guaranteed."""
    current = request if request is not None else build_request()
    for _ in range(max_steps):
        response = client.chat.create(current)
        reasons: List[Optional[str]] = [
            response.finish_reason,
            *(message.finish_reason for message in response.messages),
        ]
        if any(reason in ("length", "error") for reason in reasons):
            raise RuntimeError(f"Generation stopped before completion: {reasons}")
        if not validate_parallel_calls(response):
            if current.tool_config is not None and current.tool_config.mode in ("any", "forced"):
                raise RuntimeError("The server did not honor the requested tool selection")
            return extract_final_text(response)
        current = build_follow_up_request(current, response)
    raise RuntimeError("Tool loop exceeded max_steps")


def main() -> None:
    """Run the example with configured authentication and model settings."""
    load_dotenv()
    print("Using local demonstration weather and exchange-rate data.")
    with GigaChat() as client:
        print(run(client))


if __name__ == "__main__":
    main()
