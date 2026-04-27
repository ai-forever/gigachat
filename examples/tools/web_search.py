"""Use web search with models or plain dictionaries."""

from typing import Any, Dict, List, Set, Tuple

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatTool, ChatToolConfig


def message_text(message: Any) -> str:
    """Return combined text from a chat message."""
    content = message.get("content") if isinstance(message, dict) else message.content
    if content is None:
        return ""

    parts: List[str] = []
    for part in content:
        text = part.get("text") if isinstance(part, dict) else part.text
        if text:
            parts.append(text)
    return "".join(parts)


def message_sources(message: Any) -> List[Tuple[str, str]]:
    """Return unique sources from a chat message."""
    content = message.get("content") if isinstance(message, dict) else message.content
    if content is None:
        return []

    seen: Set[Tuple[str, str]] = set()
    sources: List[Tuple[str, str]] = []
    for part in content:
        inline_data = part.get("inline_data") if isinstance(part, dict) else part.inline_data
        inline_sources = None
        if isinstance(inline_data, dict):
            inline_sources = inline_data.get("sources")
        elif inline_data is not None:
            inline_sources = inline_data.sources

        for source in (inline_sources or {}).values():
            title = source.get("title") if isinstance(source, dict) else source.title
            url = source.get("url") if isinstance(source, dict) else source.url
            key = (title or "Untitled source", url or "")
            if key not in seen:
                seen.add(key)
                sources.append(key)

    return sources


def request_with_models() -> ChatCompletionRequest:
    """Build a web-search request with SDK models."""
    return ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="What is the USD/RUB on today?",
            )
        ],
        tools=[ChatTool(web_search={})],
        tool_config=ChatToolConfig(mode="auto"),
    )


def request_with_dict() -> Dict[str, Any]:
    """Build a web-search request with a plain dict."""
    return {
        "messages": [
            {
                "role": "user",
                "content": [{"text": "What is the USD/RUB on today?"}],
            }
        ],
        "tools": ["web_search"],
        "tool_config": {"mode": "auto"},
    }


def main() -> None:
    """Run both request styles."""
    load_dotenv()

    with GigaChat() as client:
        for title, request in (
            ("Models", request_with_models()),
            ("Dict", request_with_dict()),
        ):
            response = client.chat.create(request)
            message = response.messages[0]

            print(f"\n{title}:")
            print(message_text(message))

            for source_title, url in message_sources(message):
                print(f"- {source_title}: {url}")


if __name__ == "__main__":
    main()
