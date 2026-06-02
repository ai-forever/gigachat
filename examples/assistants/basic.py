"""Create, use, and delete an assistant."""

from dotenv import load_dotenv

from examples._utils import first_message_text
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage


def main() -> None:
    """Run a short assistant lifecycle."""
    load_dotenv()

    with GigaChat() as client:
        created = client.assistants.create(
            model="GigaChat-2",
            name="SDK Example Assistant",
            instructions="Answer as a concise Python SDK maintainer.",
            description="Temporary assistant created by examples.assistants.basic.",
            metadata={"example": "assistants.basic"},
        )
        try:
            response = client.chat.create(
                ChatCompletionRequest(
                    assistant_id=created.assistant_id,
                    messages=[ChatMessage(role="user", content="How should I test a new SDK example?")],
                )
            )
        finally:
            client.assistants.delete(created.assistant_id)

    print(first_message_text(response))
    print(f"Assistant deleted: {created.assistant_id}")


if __name__ == "__main__":
    main()
