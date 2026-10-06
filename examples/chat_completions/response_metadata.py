"""Read assistant text, optional metadata, and readable API errors."""

import json
from typing import Union

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.exceptions import ResponseError
from gigachat.models import ChatCompletionResponse, PrimaryChatCompletionChunk


def print_response(response: Union[ChatCompletionResponse, PrimaryChatCompletionChunk]) -> None:
    """Print each message and metadata that is actually present."""
    for message in response.messages or []:
        for part in message.content or []:
            if part.text is not None:
                print(f"{message.role or 'delta'}: {part.text}")
            if part.inline_data is not None:
                print("Inline metadata:", part.inline_data.model_dump_json(exclude_none=True))
        if message.finish_reason is not None:
            print(f"{message.role or 'delta'} finish reason: {message.finish_reason}")
    if response.usage is not None:
        print("Usage:", response.usage.model_dump_json(exclude_none=True))
    if response.additional_data is not None:
        print("Additional metadata:", json.dumps(response.additional_data, ensure_ascii=False))
    if response.error_details is not None:
        print("Completion error:", json.dumps(response.error_details, ensure_ascii=False))
    if response.finish_reason is not None:
        print("Finish reason:", response.finish_reason)


def run(client: GigaChat) -> None:
    """Read one completion and one stream without assuming every chunk has text."""
    request = {
        "messages": [{"role": "user", "content": "Give one short tip for testing Python code."}],
        "model_options": {"max_tokens": 64},
    }
    try:
        print("Completion:")
        print_response(client.chat.create(request))
        print("\nStream:")
        for chunk in client.chat.stream(request):
            # Both named and unnamed SSE events are supported. Terminal chunks
            # can contain only usage, finish_reason, or error_details.
            print_response(chunk)
    except ResponseError as error:
        print("HTTP error:", str(error))  # UTF-8 text is decoded by the SDK.
        # error.content remains the original bytes for application handling.
        raise


def main() -> None:
    """Run the response-inspection example."""
    load_dotenv()
    with GigaChat() as client:
        run(client)


if __name__ == "__main__":
    main()
