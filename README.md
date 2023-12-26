# GigaChat. Python-библиотека для GigaChain

Библиотека Python, позволяющая [GigaChain](https://github.com/ai-forever/gigachain) обращаться к GigaChat — нейросетевой модели, которая умеет вести диалог, писать код, создавать тексты и картинки по запросу.

Обмен данными с сервисом обеспечивается с помощью GigaChat API. О том как получить доступ к API читайте в [официальной документации](https://developers.sber.ru/docs/ru/gigachat/api/integration).

Библиотека поддерживает обработку [потоковой передачи токенов](https://developers.sber.ru/docs/ru/gigachat/api/response-token-streaming), а также работу в синхронном или в асинхронном режиме.

Библиотека позволяет выполнить [точный подсчет токенов](examples/README.md) в тексте с помощью GigaChat API.

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
from gigachat import GigaChat

# Используйте токен, полученный в личном кабинете из поля Авторизационные данные
with GigaChat(credentials=..., verify_ssl_certs=False) as giga:
    response = giga.chat("Какие факторы влияют на стоимость страховки на дом?")
    print(response.choices[0].message.content)
```

> [!NOTE]
> Вы можете явно указать используемую модель с помощью параметра `model`, например `GigaChat(model='GigaChat-Pro')`
> Получить список доступных моделей можно с помощью метода `get_models()`

> [!NOTE]
> Чтобы точно вычислить сколько токенов занимают тексты, используйте метод `tokens_count(["текст1", "текст2", ...])`

> [!WARNING]
> Функция для получения эмбеддингов находится на этапе тестирования и может быть не доступна некоторым категориям пользователей.
> Для получения эмбеддингов используйте метод `embeddings("текст")`

[Больше примеров](https://github.com/ai-forever/gigachat/blob/dev/examples/README.md).

## Способы авторизации

Авторизация с помощью токена (в личном кабинете из поля Авторизационные данные):

```py
giga = GigaChat(credentials=...)

# Личное пространство
giga = GigaChat(credentials=..., scope="GIGACHAT_API_PERS")

# Корпоративное пространство
giga = GigaChat(credentials=..., scope="GIGACHAT_API_CORP")
```

Авторизация с помощью логина и пароля:

```py
giga = GigaChat(
    base_url="https://gigachat.devices.sberbank.ru/api/v1",
    user=...,
    password=...,
)
```

Взаимная аутентификация по протоколу TLS (mTLS):

```py
giga = GigaChat(
    base_url="https://gigachat.devices.sberbank.ru/api/v1",
    ca_bundle_file="certs/ca.pem",  # chain_pem.txt
    cert_file="certs/tls.pem",  # published_pem.txt
    key_file="certs/tls.key",
    key_file_password="123456",
)
```

Авторизация с помощью временного токена

## Дополнительные настройки

Отключение проверки сертификатов:

```py
giga = GigaChat(verify_ssl_certs=False)
```

> [!WARNING]
> Отключение проверки сертификатов снижает безопасность обмена данными.


Установка корневого сертификата "Минцифры России":
```bash
curl -k "https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer" -w "\n" >> $(python -m certifi)
```

### Настройки в переменных окружения

Чтобы задать настройки с помощью переменных окружения, используйте префикс `GIGACHAT_`.

Авторизация с помощью токена и отключение проверки сертификатов:

```sh
export GIGACHAT_CREDENTIALS=...
export GIGACHAT_SCOPE=...
export GIGACHAT_VERIFY_SSL_CERTS=False
```

Авторизация с помощью логина и пароля:

```sh
export GIGACHAT_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1
export GIGACHAT_USER=...
export GIGACHAT_PASSWORD=...
```
