import os

from gigachat import GigaChat

if "GIGACHAT_CREDENTIALS" not in os.environ:
    os.environ["GIGACHAT_CREDENTIALS"] = input("GigaChat Credentials: ")

if "GIGACHAT_SCOPE" not in os.environ:
    os.environ["GIGACHAT_SCOPE"] = input("GigaChat Scope: ")


client = GigaChat(verify_ssl_certs=False)

text = """Cats are cute and fluffy pets that belong to the cat family.
They are known for their friendly nature, playfulness and soft fur.
Cats can be of different breeds, each with its own unique characteristics.
And this text was definitely not written by a neural network,
because I'm writing it. I don't have much to say about cats,
except that they are soft and fluffy, purring creatures.
These animals have become popular due to their ability to lift people's spirits
and create a cozy atmosphere in the home."""
ai_result = client.check_ai(text, "GigaCheckDetection")
print(ai_result)
