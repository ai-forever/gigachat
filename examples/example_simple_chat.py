"""Example of working with chat"""

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

payload = Chat(
    messages=[
        Messages(
            role=MessagesRole.SYSTEM,
            content="You are an attentive bot-psychologist who helps the user solve their problems.",
        )
    ],
    temperature=0.7,
    max_tokens=100,
)

with GigaChat(verify_ssl_certs=False) as giga:
    while True:
        user_input = input("User: ")
        payload.messages.append(Messages(role=MessagesRole.USER, content=user_input))
        response = giga.chat(payload)
        payload.messages.append(response.choices[0].message)
        print("Bot: ", response.choices[0].message.content)
