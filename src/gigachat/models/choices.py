from typing import Optional

from gigachat.models.messages_res import MessagesRes
from gigachat.pydantic_v1 import BaseModel


class Choices(BaseModel):
    message: MessagesRes
    index: int
    finish_reason: Optional[str] = None
