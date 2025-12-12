from typing import List

from pydantic import Field

from gigachat.models.base import APIResponse


class Model(APIResponse):
    """Model description."""

    id_: str = Field(alias="id", description="Model identifier (name).")
    object_: str = Field(alias="object", description="Object type.")
    owned_by: str = Field(description="Owner of the model.")


class Models(APIResponse):
    """List of available models."""

    data: List[Model] = Field(description="List of model objects.")
    object_: str = Field(alias="object", description="Object type.")
