from typing import List, Optional

from pydantic import BaseModel, Field

from gigachat.models.utils import WithXHeaders


class EmbeddingsUsage(BaseModel):
    """Usage statistics for embeddings."""

    prompt_tokens: int
    """Number of tokens in the input text."""


class Embedding(BaseModel):
    """Embedding object."""

    embedding: List[float]
    """Embedding vector."""
    usage: EmbeddingsUsage
    """Usage statistics."""
    index: int
    """Index of the embedding in the list."""
    object_: str = Field(alias="object")
    """Object type."""


class Embeddings(WithXHeaders):
    """Embeddings response."""

    data: List[Embedding]
    """List of embedding objects."""
    model: Optional[str] = None
    """Model name used for embedding generation."""
    object_: str = Field(alias="object")
    """Object type."""
