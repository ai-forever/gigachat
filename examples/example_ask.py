"""Question-answer example"""

from gigachat import GigaChat

# Use the token obtained from the personal account in the credentials field
with GigaChat(credentials=..., verify_ssl_certs=False) as giga:
    response = giga.chat("What factors affect the cost of home insurance?")
    print(response.choices[0].message.content)
