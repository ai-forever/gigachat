import base64
import os

from gigachat import GigaChat
from gigachat.models import Image

if "GIGACHAT_CREDENTIALS" not in os.environ:
    os.environ["GIGACHAT_CREDENTIALS"] = input("GigaChat Credentials: ")

if "GIGACHAT_SCOPE" not in os.environ:
    os.environ["GIGACHAT_SCOPE"] = input("GigaChat Scope: ")


def get_image(file_path: str = "./giga_img.jpg"):
    with GigaChat(verify_ssl_certs=False) as giga:
        response: Image = giga.get_image(file_id=...)

        # Save image to file
        with open(file_path, mode="wb") as fd:
            fd.write(base64.b64decode(response.content))


async def get_image_async(file_path: str = "./giga_img.jpg"):
    from aiofile import async_open

    async with GigaChat(verify_ssl_certs=False) as giga:
        response: Image = await giga.aget_image(file_id=...)

        # Save image to file
        async with async_open(file_path, "wb") as afp:
            await afp.write(base64.b64decode(response.content))
