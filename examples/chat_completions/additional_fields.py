"""Pass additional request fields through either chat API version."""

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models import Chat, ChatCompletionRequest, ChatMessage, Messages, MessagesRole


def v1_request() -> Chat:
    """Build a v1 request with an extra body parameter."""
    return Chat(
        messages=[Messages(role=MessagesRole.USER, content="Say hello in one short sentence.")],
        additional_fields={"max_tokens": 32},
    )


def v2_request() -> ChatCompletionRequest:
    """Build a v2 request with extra body parameters at their wire location."""
    return ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Say hello in one short sentence.")],
        additional_fields={"model_options": {"max_tokens": 32}},
    )


def main() -> None:
    """Send one request to each API version."""
    load_dotenv()
    # Use ordinary, supported options to demonstrate the escape hatch without
    # requiring special permissions. Prefer typed fields for everyday options.
    # Additional fields keep their exact API nesting; there is no wire wrapper.
    # The merge is shallow, and serialized non-null explicit fields win.
    with GigaChat() as client:
        print("v1:")
        print(client.chat(v1_request()).model_dump_json(indent=2, by_alias=True, exclude_none=True))
        print("v2:")
        print(client.chat.create(v2_request()).model_dump_json(indent=2, by_alias=True, exclude_none=True))


if __name__ == "__main__":
    main()
