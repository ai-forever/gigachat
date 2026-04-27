"""Generate an image with the built-in image tool."""

from dotenv import load_dotenv

from examples._utils import first_message_text, message_file_ids
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatTool, ChatToolConfig


def main() -> None:
    """Run an image generation request."""
    load_dotenv()

    request = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Create a simple square icon concept for a Python SDK release.",
            )
        ],
        tools=[ChatTool(image_generate={})],
        tool_config=ChatToolConfig(mode="forced", tool_name="image_generate"),
    )

    with GigaChat() as client:
        response = client.chat.create(request)

    print(first_message_text(response))
    for file_id in message_file_ids(response.messages[0]):
        print(f"Generated file: {file_id}")


if __name__ == "__main__":
    main()
