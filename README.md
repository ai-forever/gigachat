# GigaChat. Python-библиотека для GigaChain

Библиотека Python, позволяющая [GigaChain](https://github.com/ai-forever/gigachain) обращаться к GigaChat — нейросетевой модели, которая умеет вести диалог, писать код, создавать тексты и картинки по запросу.

Обмен данными с сервисом обеспечивается с помощью GigaChat API. О том как получить доступ к API читайте в [официальной документации](https://developers.sber.ru/docs/ru/gigachat/api/integration).

Библиотека поддерживает обработку [потоковой передачи токенов](https://developers.sber.ru/docs/ru/gigachat/api/response-token-streaming), а также работу в синхронном или в асинхронном режиме.

Библиотека позволяет выполнить [точный подсчет токенов](examples/README.md) в тексте с помощью GigaChat API.

> [!WARNING]
> В версии 0.1.14 добавлена поддержка функций (functions). Данная опция находится на этапе тестирования и пока доступна только для
> некоторых моделей, а протокол может быть изменен в следующих версиях.

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
with GigaChat(credentials=<авторизационные данные>, verify_ssl_certs=False) as giga:
    response = giga.chat("Какие факторы влияют на стоимость страховки на дом?")
    print(response.choices[0].message.content)
```

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

### Выбор модели

С помощью GigaChain вы можете обращаться к различным моделям, которые предоставляет GigaChat.

Для этого передайте название модели в параметре `model`:

```py
giga = GigaChat(model="GigaChat-Pro")
```

Полный список доступных моделей можно получить с помощью запроса [`GET /models`](https://developers.sber.ru/docs/ru/gigachat/api/reference#get-models) к GigaChat API.

> [!WARNING]
> Стоимость запросов к разным моделям отличается. Подробную информацию о тарификации запросов к той или иной модели вы ищите в [официальной документации](https://developers.sber.ru/docs/ru/gigachat/api/tariffs).

### Подсчет количества токенов

Для подсчета количества токенов в запросах используйте метод `tokens_count(["текст1", "текст2", ...])`.

Метод выполняет запрос [`POST /tokens/count`](https://developers.sber.ru/docs/ru/gigachat/api/reference#post-tokens-count) к GigaChat API и возвращает список объектов с информацией о количестве токенов в каждой строке.

### Векторное представление текста

Эмбеддинг (англ. embedding) — это вектор, представленный в виде массива чисел, который получается в результате преобразования данных, например, текста. Комбинация этих чисел, составляющих вектор, действует как многомерная карта для измерения сходства.

Для получения эмбеддингов используйте метод `embeddings("текст")`.

> [!WARNING]
> Функция получения эмбеддингов находится на этапе тестирования и может быть недоступна некоторым категориям пользователей.

### Отключение проверки сертификатов

Для отключения проверки сертификатов передайте параметр `verify_ssl_certs=False`:

```py
giga = GigaChat(verify_ssl_certs=False)
```

> [!WARNING]
> Отключение проверки сертификатов снижает безопасность обмена данными.


### Установка корневого сертификата НУЦ Минцифры:

Для установка корневого сертификата НУЦ Минцифры выполните команду:

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
