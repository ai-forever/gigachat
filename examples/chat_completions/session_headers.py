"""Set a default session header and temporarily override it for a request."""

import os
from typing import List
from uuid import uuid4

from dotenv import load_dotenv

from gigachat import GigaChat, session_id_cvar
from gigachat.models import ChatCompletionResponse


def run(client: GigaChat) -> List[ChatCompletionResponse]:
    """Send with the default, overridden, and restored session identifiers."""
    request = {"messages": [{"role": "user", "content": "Say hello."}], "model_options": {"max_tokens": 32}}
    responses = [client.chat.create(request)]
    token = session_id_cvar.set(str(uuid4()))
    try:
        responses.append(client.chat.create(request))
    finally:
        session_id_cvar.reset(token)
    responses.append(client.chat.create(request))
    return responses


def main() -> None:
    """Show session response headers and usage without assuming a cache hit."""
    load_dotenv()
    session_id = os.getenv("GIGACHAT_SESSION_ID") or str(uuid4())
    with GigaChat(session_id=session_id) as client:
        for label, response in zip(("Default session", "Temporary session", "Restored session"), run(client)):
            print(f"\n{label}:")
            print("Response headers:", response.x_headers)
            if response.usage is not None:
                print(response.usage.model_dump_json(exclude_none=True))


if __name__ == "__main__":
    main()
