from typing import Optional

from gigachat.models.messages_chunk import MessagesChunk
from gigachat.pydantic_v1 import BaseModel


class ChoicesChunk(BaseModel):
    delta: MessagesChunk
    index: int = 0
    finish_reason: Optional[str] = None
