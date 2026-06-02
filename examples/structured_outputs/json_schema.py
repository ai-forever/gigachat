"""Request JSON output with an explicit JSON Schema."""

from dotenv import load_dotenv

from examples._utils import first_message_text
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatModelOptions, ChatResponseFormat

RELEASE_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "checks": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3,
        },
    },
    "required": ["version", "checks"],
    "additionalProperties": False,
}


def main() -> None:
    """Run a JSON Schema response-format request."""
    load_dotenv()

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Return a release checklist for SDK version 0.3.0.")],
        model_options=ChatModelOptions(
            response_format=ChatResponseFormat(type="json_schema", schema=RELEASE_SCHEMA, strict=True)
        ),
    )

    with GigaChat() as client:
        response = client.chat.create(request)

    print(first_message_text(response))


if __name__ == "__main__":
    main()
