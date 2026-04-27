"""Reuse stored thread context."""

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatStorage


def message_text(message: ChatMessage) -> str:
    """Return combined text from a chat message."""
    if message.content is None:
        return ""

    return "".join([part.text for part in message.content if part.text])


def main() -> None:
    """Run a two-step thread example."""
    load_dotenv()

    first_request = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="My name is Alex. Remember it for the next question.",
            )
        ],
        storage=ChatStorage(),
    )

    with GigaChat() as client:
        first_response = client.chat.create(first_request)
        print(message_text(first_response.messages[0]))

        second_response = client.chat.create(
            ChatCompletionRequest(
                messages=[
                    ChatMessage(
                        role="user",
                        content="What is my name?",
                    )
                ],
                storage=ChatStorage(thread_id=first_response.thread_id),
            )
        )

    print(message_text(second_response.messages[0]))
    print(f"Thread ID: {first_response.thread_id}")


if __name__ == "__main__":
    main()
