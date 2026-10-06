"""Reuse stored thread context and one session identifier."""

import os
from typing import Tuple
from uuid import uuid4

from dotenv import load_dotenv

from examples._utils import first_message_text
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatModelOptions, ChatStorage


def run(client: GigaChat) -> Tuple[ChatCompletionResponse, ChatCompletionResponse]:
    """Create a stored conversation and continue with only the new message."""
    first_response = client.chat.create(
        ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="My name is Alex. Remember it for the next question.")],
            storage=ChatStorage(),
            model_options=ChatModelOptions(max_tokens=64),
        )
    )
    if not first_response.thread_id:
        raise RuntimeError("The server did not return a thread_id; cannot continue a stored conversation")
    # Do not send model again. The stored thread selects it, even if the client
    # has a configured default. A session header alone does not store history.
    second_response = client.chat.create(
        ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="What is my name?")],
            storage=ChatStorage(thread_id=first_response.thread_id),
            model_options=ChatModelOptions(max_tokens=64),
        )
    )
    return first_response, second_response


def main() -> None:
    """Run a two-request conversation using server-side history."""
    load_dotenv()
    session_id = os.getenv("GIGACHAT_SESSION_ID") or str(uuid4())
    with GigaChat(session_id=session_id) as client:
        first, second = run(client)
    print(first_message_text(first))
    print(first_message_text(second))
    print(f"Thread ID: {first.thread_id}")


if __name__ == "__main__":
    main()
