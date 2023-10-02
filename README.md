## GigaChat Python Library

GigaChat - мультимодальная нейросетевая модель. Умеет отвечать на вопросы, вести диалог и писать код

> [!NOTE]
> О том как подключить GigaChat читайте в [официальной документации](https://developers.sber.ru/docs/ru/gigachat/api/integration).

Модуль поддерживает работу как в синхронном, так и в асинхронном режиме. Кроме этого модуль поддерживает обработку [потоковой передачи токенов](https://developers.sber.ru/docs/ru/gigachat/api/response-token-streaming).

## Установка

Библиотеку можно установить с помощью pip:

```sh
pip install gigachat
```
## Работа с GigaChat:

Вот простой пример работы с чатом с помощью модуля:

```py
"""Пример работы с чатом"""
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole


payload = Chat(
    messages=[
        Messages(
            role=MessagesRole.SYSTEM,
            content="Ты эмпатичный бот-психолог, который помогает пользователю решить его проблемы."
        )
    ],
    temperature=0.7,
    max_tokens=100,
)

# используйте данные из поля Авторизационные данные
with GigaChat(credentials=..., verify_ssl_certs=False) as giga:
    while True:
        user_input = input("User: ")
        payload.messages.append(Messages(role=MessagesRole.USER, content=user_input))
        response = giga.chat(payload)
        payload.messages.append(response.choices[0].message)
        print("Bot: ", response.choices[0].message.content)
```

> [!NOTE]
> Для начала использования:
>1. [Подключите](https://developers.sber.ru/link/gc-api) сервис GigaChat
>2. В созданном проекте GigaChat сгенерируйте _**Client Secret**_ и сохраните данные из поля _**Авторизационные данные**_


Больше примеров в [examples](https://github.com/ai-forever/gigachat/tree/main/examples).


Авторизация по логину и паролю
```py
giga = GigaChat(
    base_url="https://beta.saluteai.sberdevices.ru/v1",
    user=...,
    password=...,
)
```

По ранее полученному access_token
```py
giga = GigaChat(access_token=...)
```

Отключаем авторизацию (например когда авторизация средствами service mesh istio)
```py
giga = GigaChat(use_auth=False)
```

Отключаем проверку сертификатов (небезопасно)
```py
giga = GigaChat(verify_ssl_certs=False)
```

Настройки можно задать через переменные окружения используется префикс GIGACHAT_
```sh
export GIGACHAT_CREDENTIALS=...
export GIGACHAT_VERIFY_SSL_CERTS=False
```

```sh
export GIGACHAT_BASE_URL=https://beta.saluteai.sberdevices.ru/v1
export GIGACHAT_USER=...
export GIGACHAT_PASSWORD=...
```
