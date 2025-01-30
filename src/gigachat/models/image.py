from gigachat.models.with_x_headers import WithXHeaders


class Image(WithXHeaders):
    """Изображение"""

    content: str
    """Изображение в base64 кодировке"""
