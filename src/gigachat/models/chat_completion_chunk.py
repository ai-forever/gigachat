from typing import List

from gigachat.models.choices_chunk import ChoicesChunk
from gigachat.pydantic_v1 import BaseModel, Field


class ChatCompletionChunk(BaseModel):
    choices: List[ChoicesChunk]
    created: int
    model: str
    object_: str = Field(alias="object")
