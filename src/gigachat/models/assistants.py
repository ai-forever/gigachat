from typing import Any

from pydantic import BaseModel, Field

from gigachat.models.base import APIResponse
from gigachat.models.chat import Function


class AssistantAttachment(BaseModel):
    """File attached to an assistant."""

    file_id: str = Field(description="Identifier of the file attached to the assistant.")
    name: str = Field(description="Name of the file attached to the assistant.")


class Assistant(BaseModel):
    """Assistant object."""

    model: str = Field(description="ID of the model to be used.")
    assistant_id: str = Field(description="The ID of the assistant (UUIDv4).")
    name: str | None = Field(default=None, description="The name of the assistant.")
    description: str | None = Field(default=None, description="The description of the assistant.")
    instructions: str | None = Field(default=None, description="The system instructions that the assistant uses.")
    created_at: int = Field(description="The time at which the assistant was created (Unix timestamp).")
    updated_at: int = Field(description="The time at which the assistant was last updated (Unix timestamp).")
    files: list[AssistantAttachment] | None = Field(default=None, description="Files attached to the assistant.")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Set of 16 key-value pairs that can be attached to an object."
    )
    threads_count: int | None = Field(default=None, description="Number of threads interacting with this assistant.")
    functions: list[Function] | None = Field(default=None, description="List of functions available to the assistant.")


class Assistants(APIResponse):
    """List of assistants."""

    data: list[Assistant] = Field(description="List of assistant objects.")


class AssistantDelete(APIResponse):
    """Assistant deletion response."""

    assistant_id: str = Field(description="The ID of the assistant.")
    deleted: bool = Field(description="Deletion status. True if deleted.")


class AssistantFileDelete(APIResponse):
    """Assistant file deletion response."""

    file_id: str = Field(description="The ID of the file.")
    deleted: bool = Field(description="Deletion status. True if deleted.")


class CreateAssistant(APIResponse):
    """Response for assistant creation."""

    assistant_id: str = Field(description="The ID of the created assistant (UUIDv4).")
    created_at: int = Field(description="The time at which the assistant was created (Unix timestamp).")
