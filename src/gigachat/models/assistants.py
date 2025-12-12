from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from gigachat.models.base import APIResponse
from gigachat.models.chat import Function


class AssistantAttachment(BaseModel):
    """File attached to an assistant."""

    file_id: str
    """Identifier of the file attached to the assistant."""
    name: str
    """Name of the file attached to the assistant."""


class Assistant(BaseModel):
    """Assistant object."""

    model: str
    """ID of the model to be used."""
    assistant_id: str
    """The ID of the assistant (UUIDv4)."""
    name: Optional[str] = None
    """The name of the assistant."""
    description: Optional[str] = None
    """The description of the assistant."""
    instructions: Optional[str] = None
    """The system instructions that the assistant uses."""
    created_at: int
    """The time at which the assistant was created (Unix timestamp)."""
    updated_at: int
    """The time at which the assistant was last updated (Unix timestamp)."""
    files: Optional[List[AssistantAttachment]] = None
    """Files attached to the assistant."""
    metadata: Optional[Dict[str, Any]] = None
    """Set of 16 key-value pairs that can be attached to an object."""
    threads_count: Optional[int] = None
    """Number of threads interacting with this assistant."""
    functions: Optional[List[Function]] = None
    """List of functions available to the assistant."""


class Assistants(APIResponse):
    """List of assistants."""

    data: List[Assistant]
    """List of assistant objects."""


class AssistantDelete(APIResponse):
    """Assistant deletion response."""

    assistant_id: str
    """The ID of the assistant."""
    deleted: bool
    """Deletion status. True if deleted."""


class AssistantFileDelete(APIResponse):
    """Assistant file deletion response."""

    file_id: str
    """The ID of the file."""
    deleted: bool
    """Deletion status. True if deleted."""


class CreateAssistant(APIResponse):
    """Response for assistant creation."""

    assistant_id: str
    """The ID of the created assistant (UUIDv4)."""
    created_at: int
    """The time at which the assistant was created (Unix timestamp)."""
