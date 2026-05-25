"""Upload a file and reference it in a chat-completions request."""

from dotenv import load_dotenv

from examples._utils import first_message_text
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage

FILE_TEXT = """GigaChat SDK test note
- Primary chat surface is available as client.chat.create().
- Built-in tools are passed through the tools field.
- Stateful context is configured through storage.
"""


def main() -> None:
    """Upload a text file and ask the model about it."""
    load_dotenv()

    with GigaChat() as client:
        uploaded = client.upload_file(file=("sdk_notes.txt", FILE_TEXT.encode("utf-8")))
        response = client.chat.create(
            ChatCompletionRequest(
                messages=[
                    ChatMessage(
                        role="user",
                        content=[
                            {"text": "Summarize this file in two bullets."},
                            {"files": [{"id": uploaded.id_}]},
                        ],
                    )
                ]
            )
        )

    print(first_message_text(response))
    print(f"Uploaded file: {uploaded.id_}")


if __name__ == "__main__":
    main()
