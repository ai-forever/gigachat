"""Пример подсчета токенов в тексте"""
from gigachat import GigaChat

# Используйте токен, полученный в личном кабинете из поля Авторизационные данные
with GigaChat(credentials=..., verify_ssl_certs=False, model='GigaChat-Pro', ) as giga:
    result = giga.tokens_count(input=["12345"], model="GigaChat-Pro")
    print(result)
