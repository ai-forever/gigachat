from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from gigachat.models.base import APIResponse


class EmbeddingsUsage(BaseModel):
    """Usage statistics for embeddings."""

    prompt_tokens: int = Field(description="Number of tokens in the input text.")


class Embedding(BaseModel):
    """Embedding object."""

    embedding: list[float] | str = Field(description="Embedding vector.")
    truncated: bool | None = None
    usage: EmbeddingsUsage = Field(description="Usage statistics.")
    index: int = Field(description="Index of the embedding in the list.")
    object_: str = Field(alias="object", description="Object type.")


class EmbeddingError(BaseModel):
    """Describe an input rejected during embedding generation."""

    model_config = ConfigDict(extra="allow")
    object_: Literal["error"] = Field(alias="object")
    index: int
    error: Any


class Embeddings(APIResponse):
    """Embeddings response."""

    data: list[Embedding | EmbeddingError] = Field(description="List of embedding objects.")
    model: str | None = Field(default=None, description="Model name used for embedding generation.")
    object_: str = Field(alias="object", description="Object type.")
