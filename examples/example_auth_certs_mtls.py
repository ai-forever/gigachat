"""Взаимная аутентификация по протоколу TLS (mTLS)"""

from gigachat import GigaChat

with GigaChat(
    base_url="https://gigachat.devices.sberbank.ru/api/v1",
    ca_bundle_file="certs/ca.pem",
    cert_file="certs/tls.pem",
    key_file="certs/tls.key",
    key_file_password="123456",
) as giga:
    response = giga.chat("Какие факторы влияют на стоимость страховки на дом?")
    print(response.choices[0].message.content)
