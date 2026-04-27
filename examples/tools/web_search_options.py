"""Configure the built-in web-search tool."""

from dotenv import load_dotenv

from examples._utils import first_message_text, message_sources
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatTool, ChatToolConfig, ChatWebSearchTool


def main() -> None:
    """Run a web-search request with explicit search mode."""
    load_dotenv()

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="What is new in the latest stable Python release?")],
        tools=[ChatTool(web_search=ChatWebSearchTool(type="actual_info_web_search"))],
        tool_config=ChatToolConfig(mode="auto"),
    )

    with GigaChat() as client:
        response = client.chat.create(request)

    message = response.messages[0]
    print(first_message_text(response))
    for title, url in message_sources(message):
        print(f"- {title}: {url}")


if __name__ == "__main__":
    main()
