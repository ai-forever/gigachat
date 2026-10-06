"""Bound reasoning and final-answer generation in v1 and v2 requests."""

from typing import Any, Dict

from dotenv import load_dotenv

from examples._utils import message_text
from gigachat import GigaChat
from gigachat.models import (
    Chat,
    ChatCompletionRequest,
    ChatMessage,
    ChatModelOptions,
    ChatReasoning,
    Messages,
    MessagesRole,
)

PROMPT = "A train travels 120 km in 2 hours. What is its average speed?"


def request_with_models() -> ChatCompletionRequest:
    """Build a v2 request with separate reasoning and overall token limits."""
    return ChatCompletionRequest(
        messages=[ChatMessage(role="user", content=PROMPT)],
        model_options=ChatModelOptions(
            max_tokens=512,
            reasoning=ChatReasoning(effort="medium", max_tokens=128),
        ),
    )


def request_with_dict() -> Dict[str, Any]:
    """Build the same v2 request as a plain dictionary."""
    return {
        "messages": [{"role": "user", "content": [{"text": PROMPT}]}],
        "model_options": {"max_tokens": 512, "reasoning": {"effort": "medium", "max_tokens": 128}},
    }


def request_v1() -> Chat:
    """Build the corresponding v1 request for client.chat(request_v1())."""
    return Chat(
        messages=[Messages(role=MessagesRole.USER, content=PROMPT)],
        max_tokens=512,
        reasoning_effort="medium",
        reasoning_max_tokens=128,
    )


def main() -> None:
    """Run one v2 request using the configured model's reasoning capability."""
    load_dotenv()
    with GigaChat() as client:
        response = client.chat.create(request_with_models())
    for message in response.messages:
        print(f"{message.role}: {message_text(message)}")
        if message.finish_reason is not None:
            print("Message finish reason:", message.finish_reason)
    if response.finish_reason is not None:
        print("Finish reason:", response.finish_reason)
    if response.usage is not None:
        print("Usage:", response.usage.model_dump_json(exclude_none=True))


if __name__ == "__main__":
    main()
