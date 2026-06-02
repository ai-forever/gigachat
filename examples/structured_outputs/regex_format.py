"""Constrain the answer with a regex response format."""

from dotenv import load_dotenv

from examples._utils import first_message_text
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatModelOptions, ChatResponseFormat


def main() -> None:
    """Run a regex response-format request."""
    load_dotenv()

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Generate one support ticket code.")],
        model_options=ChatModelOptions(response_format=ChatResponseFormat(type="regex", regex=r"[A-Z]{3}-\d{4}")),
    )

    with GigaChat() as client:
        response = client.chat.create(request)

    print(first_message_text(response))


if __name__ == "__main__":
    main()
