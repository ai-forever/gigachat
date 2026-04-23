from typing import Optional

from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatMessageChunk


def _first_text(message: ChatMessage) -> Optional[str]:
    """Return the first text content part from a primary chat message."""
    if message.content is None:
        return None

    for part in message.content:
        if part.text:
            return part.text

    return None


def _first_chunk_text(message: ChatMessageChunk) -> str:
    """Return the first text content part from a primary stream chunk."""
    if message.content is None:
        return ""

    for part in message.content:
        if part.text:
            return part.text

    return ""


def main() -> None:
    """Run a minimal primary chat example."""
    request = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Write a short slogan for the GigaChat Python SDK.",
            )
        ]
    )

    with GigaChat() as client:
        response = client.chat.create(request)
        print("Primary create():")
        print(_first_text(response.messages[0]))

        print("\nPrimary stream():")
        for chunk in client.chat.stream("List three reasons to use a typed SDK."):
            if chunk.messages:
                print(_first_chunk_text(chunk.messages[0]), end="", flush=True)
        print()

        print("\nLegacy API is available under client.chat.legacy.*")


if __name__ == "__main__":
    main()
