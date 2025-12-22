"""Example of counting tokens in text"""

import os

from gigachat import GigaChat

if "GIGACHAT_CREDENTIALS" not in os.environ:
    os.environ["GIGACHAT_CREDENTIALS"] = input("GigaChat Credentials: ")

if "GIGACHAT_SCOPE" not in os.environ:
    os.environ["GIGACHAT_SCOPE"] = input("GigaChat Scope: ")

# Use the token obtained from the personal account in the credentials field
with GigaChat(
    verify_ssl_certs=False,
) as giga:
    result = giga.tokens_count(input_=["12345"], model="GigaChat-Pro")
    print(result)
