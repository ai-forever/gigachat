"""Пример работы с чатом"""
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

payload = Chat(
    messages=[
        Messages(
            role=MessagesRole.SYSTEM,
            content="Ты внимательный бот-психолог, который помогает пользователю решить его проблемы."
        )
    ],
    temperature=0.7,
    max_tokens=100,
)

# Используйте токен, полученный в личном кабинете из поля Авторизационные данные
with GigaChat(credentials=..., verify_ssl_certs=False) as giga:
    while True:
        user_input = input("User: ")
        payload.messages.append(Messages(role=MessagesRole.USER, content=user_input))
        response = giga.chat(payload)
        payload.messages.append(response.choices[0].message)
        print("Bot: ", response.choices[0].message.content)
