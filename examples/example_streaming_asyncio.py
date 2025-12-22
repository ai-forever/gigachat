import asyncio
import os
import time

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

if "GIGACHAT_CREDENTIALS" not in os.environ:
    os.environ["GIGACHAT_CREDENTIALS"] = input("GigaChat Credentials: ")

if "GIGACHAT_SCOPE" not in os.environ:
    os.environ["GIGACHAT_SCOPE"] = input("GigaChat Scope: ")

PAYLOAD = Chat(
    messages=[
        Messages(
            role=MessagesRole.SYSTEM,
            content="You are a smart AI assistant who is always ready to help the user.",
        ),
        Messages(
            role=MessagesRole.ASSISTANT,
            content="How can I help you?",
        ),
        Messages(
            role=MessagesRole.USER,
            content="Write a detailed report on Pushkin's life in Moscow",
        ),
    ],
    update_interval=0.1,
)


async def main():
    async with GigaChat(verify_ssl_certs=False) as giga:
        async for chunk in giga.astream(PAYLOAD):
            print(time.time(), chunk, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
