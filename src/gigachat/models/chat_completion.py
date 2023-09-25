from typing import List

from gigachat.models.choices import Choices
from gigachat.models.usage import Usage
from gigachat.pydantic_v1 import BaseModel, Field


class ChatCompletion(BaseModel):
    choices: List[Choices]
    created: int
    model: str
    usage: Usage
    object_: str = Field(alias="object")
