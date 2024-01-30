"""Пример получения эмбеддингов"""
from gigachat import GigaChat

# Используйте токен, полученный в личном кабинете из поля Авторизационные данные
with GigaChat(
    credentials=...,
    verify_ssl_certs=False,
) as giga:
    response = giga.embeddings(["Hello world!"])
    print(response)
