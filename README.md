# О gigachat

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ai-forever/gigachat/gigachat.yml?style=flat-square)](https://github.com/ai-forever/gigachat/actions/workflows/gigachat.yml)
[![GitHub License](https://img.shields.io/github/license/ai-forever/gigachat?style=flat-square)](https://opensource.org/license/MIT)
[![GitHub Downloads (all assets, all releases)](https://img.shields.io/pypi/dm/gigachat?style=flat-square?style=flat-square)](https://pypistats.org/packages/gigachat)
[![GitHub Repo stars](https://img.shields.io/github/stars/ai-forever/gigachat?style=flat-square)](https://star-history.com/#ai-forever/gigachat)
[![GitHub Open Issues](https://img.shields.io/github/issues-raw/ai-forever/gigachat)](https://github.com/ai-forever/gigachat/issues)

GigaChat — это Python-библиотека для работы с [REST API GigaChat](https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/gigachat-api).
Она является частью [GigaChain](https://github.com/ai-forever/gigachain) и входит в состав [langchain-gigachat](https://github.com/ai-forever/langchain-gigachat) — партнерского пакета opensource-фреймворка [LangChain](https://python.langchain.com/docs/introduction/).

Библиотека управляет авторизацией запросов и предоставляет все необходимые методы для работы с API.
Кроме этого она поддерживает:

* обработку потоковой передачи токенов;
* [работу с функциями](examples/example_functions.py);
* [создание эмбеддингов](examples/example_embeddings.py);
* работу в синхронном или в [асинхронном режиме](examples/streaming_asyncio.py).

> [!TIP]
> Примеры работы с библиотекой gigachat — в папке [examples](examples/README.md).

## Установка

Для установки библиотеки используйте менеджер пакетов pip:

```sh
pip install gigachat
```

## Быстрый старт

Для работы с библиотекой вам понадобится ключ авторизации API.

Чтобы получить ключ авторизации:

1. Создайте проект **GigaChat API** в личном кабинете Studio.
2. В интерфейсе проекта, в левой панели выберите раздел **Настройки API**.
3. Нажмите кнопку **Получить ключ**.

В открывшемся окне скопируйте и сохраните значение поля Authorization Key. Ключ авторизации, отображается только один раз и не хранятся в личном кабинете. При компрометации или утере ключа авторизации вы можете сгенерировать его повторно.

Подробно о том, как создать проект GigaChat API — в официальной документации, в разделах [Быстрый старт для физических лиц](https://developers.sber.ru/docs/ru/gigachat/individuals-quickstart) и [Быстрый старт для ИП и юридических лиц](https://developers.sber.ru/docs/ru/gigachat/legal-quickstart).

Передайте полученный ключ авторизации в параметре `credentials` при инициализации объекта GigaChat.

Пример показывает как отправить простой запрос на генерацию с помощью библиотеки GigaChat:

```py
from gigachat import GigaChat

# Укажите ключ авторизации, полученный в личном кабинете, в интерфейсе проекта GigaChat API
with GigaChat(credentials="ваш_ключ_авторизации", verify_ssl_certs=False) as giga:
    response = giga.chat("Какие факторы влияют на стоимость страховки на дом?")
    print(response.choices[0].message.content)
```

> [!NOTE]
> Этот и другие примеры работы с библиотекой gigachat — в папке [examples](examples/README.md).

## Параметры объекта GigaChat

В таблице описаны параметры, которые можно передать при инициализации объекта GigaChat:

| Параметр           | Обязательный | Описание                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ------------------ | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `credentials`      | да           | Ключ авторизации для обмена сообщениями с GigaChat API.<br />Ключ авторизации содержит информацию о версии API, к которой выполняются запросы. Если вы используете версию API для ИП или юрлиц, укажите это явно в параметре `scope`                                                                                                                                                                                                                                                                                                                   |
| `verify_ssl_certs` | нет          | Отключение проверки ssl-сертификатов.<br /><br />Для обращения к GigaChat API нужно [установить корневой сертификат НУЦ Минцифры](#установка-корневого-сертификата-нуц-минцифры).<br /><br />Используйте параметр ответственно, так как отключение проверки сертификатов снижает безопасность обмена данными                                                                                                                                                                                                                                                                                                                                                                                           |
| `scope`            | нет          | Версия API, к которой будет выполнен запрос. По умолчанию запросы передаются в версию для физических лиц. Возможные значения:<ul><li>`GIGACHAT_API_PERS` — версия API для физических лиц;</li><li>`GIGACHAT_API_B2B` — версия API для ИП и юрлиц при работе по предоплате.</li><li>`GIGACHAT_API_CORP` — версия API для ИП и юрлиц при работе по постоплате.</li></ul>                                                                                                                                                                                 |
| `model`            | нет          | необязательный параметр, в котором можно явно задать [модель GigaChat](https://developers.sber.ru/docs/ru/gigachat/models). Вы можете посмотреть список доступных моделей с помощью метода `get_models()`, который выполняет запрос [`GET /models`](https://developers.sber.ru/docs/ru/gigachat/api/reference#get-models).<br /><br />Стоимость запросов к разным моделям отличается. Подробную информацию о тарификации запросов к той или иной модели вы ищите в [официальной документации](https://developers.sber.ru/docs/ru/gigachat/api/tariffs) |
| `base_url`         | нет          | Адрес API. По умолчанию запросы отправляются по адресу `https://gigachat.devices.sberbank.ru/api/v1/`, но если вы хотите использовать [модели в раннем доступе](https://developers.sber.ru/docs/ru/gigachat/models/preview-models), укажите адрес `https://gigachat-preview.devices.sberbank.ru/api/v1`                                                                                                                                                                                                                                                |


> ![TIP]
> Чтобы не указывать параметры при каждой инициализации, задайте их в [переменных окружения](#настройка-переменных-окружения).

## Способы авторизации

Для авторизации запросов, кроме ключа, полученного в личном кабинете, вы можете использовать:

* имя пользователя и пароль для доступа к сервису;
* сертификаты TLS;
* токен доступа (access token), полученный в обмен на ключ авторизации в запросе [`POST /api/v2/oauth`](https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/post-token).

Для этого передайте соответствующие параметры при инициализации.

Пример авторизации с помощью логина и пароля:

```py
giga = GigaChat(
    base_url="https://gigachat.devices.sberbank.ru/api/v1",
    user="имя_пользоваеля",
    password="пароль",
)
```

Авторизация с помощью сертификатов по протоколу TLS (mTLS):

```py
giga = GigaChat(
    base_url="https://gigachat.devices.sberbank.ru/api/v1",
    ca_bundle_file="certs/ca.pem",  # chain_pem.txt
    cert_file="certs/tls.pem",  # published_pem.txt
    key_file="certs/tls.key",
    key_file_password="123456",
    ssl_context=context # optional ssl.SSLContext instance
)
```

Авторизация с помощью токена доступа: 

```py
giga = GigaChat(
    access_token="ваш_токен_доступа",
)
```

> ![NOTE]
> Токен действителен в течение 30 минут.

### Предварительная авторизация

По умолчанию, библиотека GigaChat получает токен доступа при первом запросе к API.

Если вам нужно получить токен и авторизоваться до выполнения запроса, инициализируйте объект GigaChat и вызовите метод `get_token()`.

```py
giga = GigaChat(
    base_url="https://gigachat.devices.sberbank.ru/api/v1",
    user="имя_пользователя",
    password="пароль",
)
giga.get_token()
```

## Установка корневого сертификаты НУЦ Минцифры

Чтобы библиотека GigaChat могла передавать запросы в GigaChat API, вам нужно установить корневой сертификат НУЦ Минцифры.

Для этого выполните команду:

```bash
curl -k "https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer" -w "\n" >> $(python -m certifi)
```

Вы также можете отключить проверку сертификатов с помощью параметра `verify_ssl_certs=False`, который передается при инициализации.

```py
giga = GigaChat(
    credentials="ключ_авторизации",
    verify_ssl_certs=False
)
```

> ![WARNING]
> Отключение проверки сертификатов снижает безопасность обмена данными.

## Настройка переменных окружения

Чтобы задать параметры с помощью переменных окружения, в названии переменной используйте префикс `GIGACHAT_`.

Пример переменных окружения, которые задают ключ авторизации, версию API и отключают проверку сертификатов.

```sh
export GIGACHAT_CREDENTIALS=...
export GIGACHAT_SCOPE=...
export GIGACHAT_VERIFY_SSL_CERTS=False
```

Пример переменных окружения, которые задают адрес API, имя пользователя и пароль.

```sh
export GIGACHAT_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1
export GIGACHAT_USER=...
export GIGACHAT_PASSWORD=...
```
