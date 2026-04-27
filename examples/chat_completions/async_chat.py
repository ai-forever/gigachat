"""Send an async primary chat-completions request."""

import asyncio

from dotenv import load_dotenv

from examples._utils import first_message_text
from gigachat import GigaChat


async def main() -> None:
    """Run an async request."""
    load_dotenv()

    async with GigaChat() as client:
        response = await client.achat.create("Give a one-sentence overview of async SDK clients.")

    print(first_message_text(response))


if __name__ == "__main__":
    asyncio.run(main())
