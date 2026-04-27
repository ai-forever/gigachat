"""Tune generation through model_options."""

from dotenv import load_dotenv

from examples._utils import first_message_text
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatModelOptions


def main() -> None:
    """Run a request with sampling and length options."""
    load_dotenv()

    request = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Write three short changelog bullets for a Python SDK release.",
            )
        ],
        model_options=ChatModelOptions(
            temperature=0.2,
            top_p=0.9,
            max_tokens=180,
            repetition_penalty=1.05,
        ),
    )

    with GigaChat() as client:
        response = client.chat.create(request)

    print(first_message_text(response))
    if response.usage is not None:
        print(response.usage.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
