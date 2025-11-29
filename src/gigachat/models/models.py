from typing import List

from pydantic import Field

from gigachat.models.utils import WithXHeaders


class Model(WithXHeaders):
    """Model description."""

    id_: str = Field(alias="id")
    """Model identifier (name)."""
    object_: str = Field(alias="object")
    """Object type."""
    owned_by: str
    """Owner of the model."""


class Models(WithXHeaders):
    """List of available models."""

    data: List[Model]
    """List of model objects."""
    object_: str = Field(alias="object")
    """Object type."""
