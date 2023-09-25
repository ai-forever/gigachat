from typing import List

from gigachat.models.model import Model
from gigachat.pydantic_v1 import BaseModel, Field


class Models(BaseModel):
    data: List[Model]
    object_: str = Field(alias="object")
