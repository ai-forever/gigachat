from gigachat.pydantic_v1 import BaseModel


class Image(BaseModel):
    """Изображение"""

    content: bytes
    """Изображение"""
