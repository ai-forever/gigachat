import os

from gigachat import GigaChat

if "GIGACHAT_CREDENTIALS" not in os.environ:
    os.environ["GIGACHAT_CREDENTIALS"] = input("GigaChat Credentials: ")

if "GIGACHAT_SCOPE" not in os.environ:
    os.environ["GIGACHAT_SCOPE"] = input("GigaChat Scope: ")


client = GigaChat(
    verify_ssl_certs=False,
    timeout=600,
    model="GigaChat-2-Max"
)

file = client.upload_file(open("cat.jpg", "rb"))

result = client.chat(
    {
        "messages": [
            {
                "role": "user",
                "content": "What color is the cat in the photo?",
                "attachments": [file.id_],
            }
        ],
        "temperature": 0.1,
    }
)

print(result.choices[0].message.content)
