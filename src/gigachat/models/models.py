from pydantic import ConfigDict, Field

from gigachat.models.base import APIResponse


class Model(APIResponse):
    """Model description."""

    model_config = ConfigDict(extra="allow")

    type: str | None = None
    features: list[str] | None = None
    id_: str = Field(alias="id", description="Model identifier (name).")
    object_: str = Field(alias="object", description="Object type.")
    owned_by: str = Field(description="Owner of the model.")


class Models(APIResponse):
    """List of available models."""

    data: list[Model] = Field(description="List of model objects.")
    object_: str = Field(alias="object", description="Object type.")
