import asyncio
import time

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

PAYLOAD = Chat(
    messages=[
        Messages(
            role=MessagesRole.SYSTEM,
            content="Ты - умный ИИ ассистент, который всегда готов помочь пользователю.",
        ),
        Messages(
            role=MessagesRole.ASSISTANT,
            content="Как я могу помочь вам?",
        ),
        Messages(
            role=MessagesRole.USER,
            content="Напиши подробный доклад на тему жизни Пушкина в Москве",
        ),
    ],
    update_interval=0.1,
)


async def main():
    async with GigaChat() as giga:
        async for chunk in giga.astream(PAYLOAD):
            print(time.time(), chunk, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
