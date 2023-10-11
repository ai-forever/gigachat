# GigaChat. Python-библиотека для GigaChain

Библиотека Python, позволяющая [GigaChain](https://github.com/ai-forever/gigachain) обращаться к GigaChat — нейросетевой модели, которая умеет вести диалог, писать код, создавать тексты и картинки по запросу. Обмен данными с сервисом обеспечивается с помощью GigaChat API. О том как получить доступ к API читайте в [официальной документации](https://developers.sber.ru/docs/ru/gigachat/api/integration).

Модуль поддерживает работу в синхронном и в асинхронном режиме, а также обработку [потоковой передачи токенов](https://developers.sber.ru/docs/ru/gigachat/api/response-token-streaming).

## Установка

Библиотеку можно установить с помощью pip:

```sh
pip install gigachat
```
## Работа с GigaChat

Перед использованием модуля:

1. [Подключите проект GigaChat API](https://developers.sber.ru/docs/ru/gigachat/api/integration).
2. В личном кабинете нажмите кнопку **Сгенерировать новый Client Secret**.

   Откроется окно **Новый Client Secret**.

3. В открывшемся окне, скопируйте и сохраните токен, указанный в поле **Авторизационные данные**.

   > [!WARNING]
   > Не закрывайте окно, пока не сохраните токен. В противном случае его нужно будет сгенерировать заново.

Пример показывает как импортировать библиотеку в [GigaChain](https://github.com/ai-forever/gigachain) и использовать ее для обращения к GigaChat:

```py
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

# Используйте токен, полученный в личном кабинете в поле Авторизационные данные
with GigaChat(credentials=..., verify_ssl_certs=False) as giga:
    while True:
        user_input = input("User: ")
        payload.messages.append(Messages(role=MessagesRole.USER, content=user_input))
        response = giga.chat(payload)
        payload.messages.append(response.choices[0].message)
        print("Bot: ", response.choices[0].message.content)
```

[Больше примеров](./examples/README.md).

## Способы авторизации

Авторизация с помощью [токена доступа GigaChat API](https://developers.sber.ru/docs/ru/gigachat/api/authorization):

```py
giga = GigaChat(access_token=...)
```

Авторизация с помощью логина и пароля:

```py
giga = GigaChat(
    base_url="https://gigachat.devices.sberbank.ru/api/v1",
    user=...,
    password=...,
)
```

## Дополнительные настройки

Отключение авторизации:

```py
giga = GigaChat(use_auth=False)
```

> [!NOTE]
> Функция может быть полезна, например, при авторизации с помощью Istio service mesh.

Отключение проверки сертификатов:

```py
giga = GigaChat(verify_ssl_certs=False)
```

> [!WARNING]
> Отключение проверки сертификатов снижает безопасность обмена данными.


### Настройки в переменных окружения

Чтобы задать настройки с помощью переменных окружения, используйте префикс `GIGACHAT_`.

Авторизация с помощью токена и отключение проверки сертификатов:

```sh
export GIGACHAT_CREDENTIALS=...
export GIGACHAT_VERIFY_SSL_CERTS=False
```

Авторизация с помощью логина и пароля:

```sh
export GIGACHAT_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1
export GIGACHAT_USER=...
export GIGACHAT_PASSWORD=...
```
