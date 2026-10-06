"""Tune generation with nested options or normalized root-level shorthand."""

from typing import Any, Dict

from dotenv import load_dotenv

from examples._utils import first_message_text
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatModelOptions

PROMPT = "Write three short changelog bullets for a Python SDK release."


def request_with_models() -> ChatCompletionRequest:
    """Build a request with generation options at their preferred wire location."""
    return ChatCompletionRequest(
        messages=[ChatMessage(role="user", content=PROMPT)],
        model_options=ChatModelOptions(temperature=0.2, top_p=0.9, max_tokens=180, repetition_penalty=1.05),
    )


def request_with_dict() -> Dict[str, Any]:
    """Build convenience input which the SDK moves under model_options."""
    return {
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 180,
        "repetition_penalty": 1.05,
    }


def main() -> None:
    """Show normalized shorthand and send one request."""
    load_dotenv()
    print("Normalized shorthand:")
    print(ChatCompletionRequest.model_validate(request_with_dict()).model_dump_json(indent=2, exclude_none=True))
    with GigaChat() as client:
        response = client.chat.create(request_with_models())
    print(first_message_text(response))
    for message in response.messages:
        if message.finish_reason is not None:
            print("Message finish reason:", message.finish_reason)
    if response.finish_reason is not None:
        print("Finish reason:", response.finish_reason)
    if response.usage is not None:
        print(response.usage.model_dump_json(indent=2, exclude_none=True))


if __name__ == "__main__":
    main()
