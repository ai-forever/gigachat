"""Parse structured output with models or plain dictionaries."""

from typing import Any, Dict, List

from dotenv import load_dotenv
from pydantic import BaseModel

from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage


class Plan(BaseModel):
    """Short plan returned by the model."""

    title: str
    steps: List[str]


def request_with_models() -> ChatCompletionRequest:
    """Build a parse request with SDK models."""
    return ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Make a two-step release plan for a Python SDK.",
            )
        ]
    )


def request_with_dict() -> Dict[str, Any]:
    """Build a parse request with a plain dict."""
    return {
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Make a two-step release plan for a Python SDK."}],
            }
        ]
    }


def main() -> None:
    """Run both request styles."""
    load_dotenv()

    with GigaChat() as client:
        for title, request in (
            ("Models", request_with_models()),
            ("Dict", request_with_dict()),
        ):
            _, parsed = client.chat.parse(request, response_format=Plan)
            print(f"\n{title}:")
            print(parsed.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
