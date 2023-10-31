"""Пример вопрос - ответ, для проверки сертификатов используем файл с корневым сертификатом Минцифры России"""
from gigachat import GigaChat

# Используйте токен, полученный в личном кабинете из поля Авторизационные данные.
# Укажите путь к файлу "https://gu-st.ru/content/Other/doc/russian_trusted_root_ca.cer"
with GigaChat(credentials=..., ca_bundle_file="russian_trusted_root_ca.cer") as giga:
    response = giga.chat("Какие факторы влияют на стоимость страховки на дом?")
    print(response.choices[0].message.content)
