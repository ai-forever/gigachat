"""Use reasoning with models or plain dictionaries."""

from typing import Any, Dict, List

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatReasoning


def message_text(message: Any) -> str:
    """Return combined text from a chat message."""
    content = message.get("content") if isinstance(message, dict) else message.content
    if content is None:
        return ""

    parts: List[str] = []
    for part in content:
        text = part.get("text") if isinstance(part, dict) else part.text
        if text:
            parts.append(text)
    return "".join(parts)


def request_with_models() -> ChatCompletionRequest:
    """Build a reasoning request with SDK models."""
    return ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Solve: a train travels 120 km in 2 hours. What is its average speed?",
            )
        ],
        model="GigaChat-2-Reasoning",
        reasoning=ChatReasoning(effort="high"),
    )


def request_with_dict() -> Dict[str, Any]:
    """Build a reasoning request with a plain dict."""
    return {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": "Solve: a train travels 120 km in 2 hours. What is its average speed?",
                    }
                ],
            }
        ],
        "reasoning": {"effort": "high"},
    }


def main() -> None:
    """Run both request styles."""
    load_dotenv()

    with GigaChat() as client:
        for title, request in (
            ("Models", request_with_models()),
            ("Dict", request_with_dict()),
        ):
            response = client.chat.create(request)
            print(f"\n{title}:")
            print(message_text(response.messages[0]))


if __name__ == "__main__":
    main()
