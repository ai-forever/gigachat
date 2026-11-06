from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gigachat.models.base import APIResponse


class BatchRequestCounts(BaseModel):
    """Batch request counts reported by the server."""

    total: int
    completed: int | None = None
    failed: int | None = None


class Batch(APIResponse):
    """Server-side batch job, with an open status string."""

    model_config = ConfigDict(extra="allow")
    id_: str = Field(alias="id")
    method: str
    request_counts: BatchRequestCounts
    status: str
    created_at: int
    updated_at: int
    output_file_id: str | None = None


class Batches(APIResponse):
    """Batch query response."""

    batches: list[Batch]

    @model_validator(mode="before")
    @classmethod
    def _normalize_list(cls, value: Any) -> Any:
        if isinstance(value, list):
            return {"batches": value}
        return value
