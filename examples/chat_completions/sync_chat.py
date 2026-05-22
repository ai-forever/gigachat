"""Send chat requests with models or plain dictionaries."""

from typing import Any, Dict, Optional

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage


def message_text(message: Any) -> Optional[str]:
    """Return the first text part from a chat message."""
    content = message.get("content") if isinstance(message, dict) else message.content
    if content is None:
        return None

    for part in content:
        text = part.get("text") if isinstance(part, dict) else part.text
        if text:
            return text

    return None


def request_with_models() -> ChatCompletionRequest:
    """Build a request with SDK models."""
    return ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Write a short slogan for the GigaChat Python SDK.",
            )
        ]
    )


def request_with_dict() -> Dict[str, Any]:
    """Build the same request with a plain dict."""
    return {
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Write a short slogan for the GigaChat Python SDK."}],
            }
        ]
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
            print(f"{title}: {message_text(response.messages[0])}")

        print("\nStream:")
        for chunk in client.chat.stream("List three reasons to use a typed SDK."):
            if chunk.messages:
                print(message_text(chunk.messages[0]) or "", end="", flush=True)
        print()


if __name__ == "__main__":
    main()
