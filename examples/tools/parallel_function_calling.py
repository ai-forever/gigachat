"""Request multiple client function calls in one model response."""

import json
from typing import List

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatFunctionSpecification,
    ChatFunctionsTool,
    ChatMessage,
    ChatModelOptions,
    ChatTool,
)
from gigachat.models.chat_completions import ChatFunctionCall


def build_request() -> ChatCompletionRequest:
    """Build a request that allows the model to call two functions in parallel."""
    return ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content=(
                    "Find the weather in Moscow and Kazan and the USD exchange rate. "
                    "Call independent functions in one step, then briefly compare the results."
                ),
            )
        ],
        model_options=ChatModelOptions(parallel_tool_calls=True, max_tokens=512),
        tools=[
            ChatTool(
                functions=ChatFunctionsTool(
                    specifications=[
                        ChatFunctionSpecification(
                            name="get_weather",
                            description="Return the weather in the specified city.",
                            parameters={
                                "type": "object",
                                "properties": {"city": {"type": "string"}},
                                "required": ["city"],
                            },
                        ),
                        ChatFunctionSpecification(
                            name="get_rate",
                            description="Return the currency exchange rate against the ruble.",
                            parameters={
                                "type": "object",
                                "properties": {"currency": {"type": "string"}},
                                "required": ["currency"],
                            },
                        ),
                    ]
                )
            )
        ],
    )


def validate_parallel_calls(response: ChatCompletionResponse) -> List[ChatFunctionCall]:
    """Collect zero or more assistant calls and check multi-call correlation IDs."""
    calls = [
        part.function_call
        for message in response.messages
        if message.role == "assistant"
        for part in message.content or []
        if part.function_call is not None
    ]
    if len(calls) > 1:
        ids = [call.id_ for call in calls]
        if any(not call_id for call_id in ids) or len(set(ids)) != len(ids):
            raise RuntimeError("Parallel function calls must have distinct, nonempty IDs")
    return calls


def main() -> None:
    """Run the parallel function-calling smoke request."""
    load_dotenv()

    with GigaChat() as client:
        response = client.chat.create(build_request())

    print(response.model_dump_json(indent=2, exclude_none=True, by_alias=True))
    calls = validate_parallel_calls(response)

    print(f"\nReceived {len(calls)} function calls (the flag does not guarantee a count)")
    for call in calls:
        arguments = json.dumps(call.arguments, ensure_ascii=False, sort_keys=True)
        print(f"- {call.id_}: {call.name}({arguments})")


if __name__ == "__main__":
    main()
