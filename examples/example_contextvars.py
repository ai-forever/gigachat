"""Пример перенаправления заголовков запроса в GigaChat"""
import gigachat.context
from gigachat import GigaChat

ACCESS_TOKEN = ...

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    # for logging
    "X-Client-ID": "8324244b-7133-4d30-a328-31d8466e5502",
    "X-Session-ID": "8324244b-7133-4d30-a328-31d8466e5502",
    "X-Request-ID": "8324244b-7133-4d30-a328-31d8466e5502",
}

with GigaChat(verify_ssl_certs=False) as giga:
    gigachat.context.authorization_cvar.set(headers.get("Authorization"))
    gigachat.context.client_id_cvar.set(headers.get("X-Client-ID"))
    gigachat.context.session_id_cvar.set(headers.get("X-Session-ID"))
    gigachat.context.request_id_cvar.set(headers.get("X-Request-ID"))

    response = giga.chat("Какие факторы влияют на стоимость страховки на дом?")
    print(response.choices[0].message.content)
