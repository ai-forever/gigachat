from pydantic import BaseModel, Field

from gigachat.models.base import APIResponse


class EmbeddingsUsage(BaseModel):
    """Usage statistics for embeddings."""

    prompt_tokens: int = Field(description="Number of tokens in the input text.")


class Embedding(BaseModel):
    """Embedding object."""

    embedding: list[float] = Field(description="Embedding vector.")
    usage: EmbeddingsUsage = Field(description="Usage statistics.")
    index: int = Field(description="Index of the embedding in the list.")
    object_: str = Field(alias="object", description="Object type.")


class Embeddings(APIResponse):
    """Embeddings response."""

    data: list[Embedding] = Field(description="List of embedding objects.")
    model: str | None = Field(default=None, description="Model name used for embedding generation.")
    object_: str = Field(alias="object", description="Object type.")
