from gigachat import GigaChat
from gigachat.models import Image


def get_image(file_path: str = './giga_img.jpg'):
    with GigaChat(credentials=...,
                  verify_ssl_certs=False) as giga:
        response: Image = giga.get_image(file_id=...)

        # Сохранить изображение в файл
        with open(file_path, mode="wb") as fd:
            fd.write(response.content)


async def get_image_async(file_path: str = './giga_img.jpg'):
    from aiofile import async_open

    async with GigaChat(credentials=...,
                        verify_ssl_certs=False) as giga:
        response: Image = await giga.aget_image(file_id=...)

    async with async_open(file_path, 'wb') as afp:
        await afp.write(response.content)