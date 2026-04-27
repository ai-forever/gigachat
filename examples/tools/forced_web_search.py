"""Force a built-in tool call."""

from dotenv import load_dotenv

from examples._utils import first_message_text, message_sources
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatTool, ChatToolConfig


def main() -> None:
    """Run web search through forced tool_config."""
    load_dotenv()

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Find current documentation for Python pathlib and summarize it.")],
        tools=[ChatTool(web_search={})],
        tool_config=ChatToolConfig(mode="forced", tool_name="web_search"),
    )

    with GigaChat() as client:
        response = client.chat.create(request)

    message = response.messages[0]
    print(first_message_text(response))
    for title, url in message_sources(message):
        print(f"- {title}: {url}")


if __name__ == "__main__":
    main()
