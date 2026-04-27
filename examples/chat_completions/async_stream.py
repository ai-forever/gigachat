"""Stream a primary chat-completions response asynchronously."""

import asyncio

from dotenv import load_dotenv

from examples._utils import message_text
from gigachat import GigaChatAsyncClient
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatModelOptions


async def main() -> None:
    """Run an async stream."""
    load_dotenv()

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="List five concise tips for testing SDK examples.")],
        model_options=ChatModelOptions(update_interval=0.2),
    )

    async with GigaChatAsyncClient() as client:
        async for chunk in client.achat.stream(request):
            if chunk.messages:
                print(message_text(chunk.messages[0]), end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
