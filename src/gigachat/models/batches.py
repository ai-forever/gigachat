from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from gigachat.models.base import APIResponse


class BatchMethod(str, Enum):
    """Batch execution method."""

    CHAT_COMPLETIONS = "chat_completions"
    EMBEDDER = "embedder"


class BatchStatus(str, Enum):
    """Batch processing status."""

    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class BatchRequestCounts(BaseModel):
    """Batch request counters."""

    total: int = Field(default=0, description="Total number of requests in the batch.")
    completed: Optional[int] = Field(default=None, description="Number of completed requests.")
    failed: Optional[int] = Field(default=None, description="Number of failed requests.")


class Batch(APIResponse):
    """Batch task metadata."""

    id_: str = Field(alias="id", description="Batch task identifier.")
    method: BatchMethod = Field(description="Method used to process tasks in the batch.")
    request_counts: BatchRequestCounts = Field(description="Request counters for the batch.")
    status: BatchStatus = Field(description="Current batch task status.")
    output_file_id: Optional[str] = Field(default=None, description="Identifier of the output file with results.")
    created_at: int = Field(description="Creation timestamp (Unix time).")
    updated_at: int = Field(description="Last update timestamp (Unix time).")


class Batches(APIResponse):
    """List of batch tasks."""

    batches: List[Batch] = Field(description="List of batch tasks.")
