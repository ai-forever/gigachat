"""Use the URL content extraction built-in tool."""

from dotenv import load_dotenv

from examples._utils import first_message_text
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatTool, ChatToolConfig


def main() -> None:
    """Extract and summarize content from a URL."""
    load_dotenv()

    request = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content=("Read https://docs.python.org/3/library/pathlib.html and list three use cases for pathlib."),
            )
        ],
        tools=[ChatTool(url_content_extraction={})],
        tool_config=ChatToolConfig(mode="forced", tool_name="url_content_extraction"),
    )

    with GigaChat() as client:
        response = client.chat.create(request)

    print(first_message_text(response))


if __name__ == "__main__":
    main()
