"""Example of getting embeddings"""

import os

from gigachat import GigaChat

if "GIGACHAT_CREDENTIALS" not in os.environ:
    os.environ["GIGACHAT_CREDENTIALS"] = input("GigaChat Credentials: ")

if "GIGACHAT_SCOPE" not in os.environ:
    os.environ["GIGACHAT_SCOPE"] = input("GigaChat Scope: ")

with GigaChat(verify_ssl_certs=False) as giga:
    response = giga.embeddings(["Hello world!"])
    print(response)
