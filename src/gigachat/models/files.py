from typing import List, Optional

from pydantic import Field

from gigachat.models.base import APIResponse


class UploadedFile(APIResponse):
    """Information about an uploaded file."""

    id_: str = Field(alias="id")
    """File identifier."""
    object_: str = Field(alias="object")
    """Object type."""
    bytes_: int = Field(alias="bytes")
    """File size in bytes."""
    created_at: int
    """Creation timestamp (Unix time)."""
    filename: str
    """Name of the file."""
    purpose: str
    """Intended purpose of the file."""
    access_policy: Optional[str] = None
    """Access policy."""


class UploadedFiles(APIResponse):
    """List of uploaded files."""

    data: List[UploadedFile]
    """List of file objects."""


class DeletedFile(APIResponse):
    """Information about a deleted file."""

    id_: str = Field(alias="id")
    """File identifier."""
    deleted: bool
    """Deletion status. True if deleted."""


class Image(APIResponse):
    """Image content."""

    content: str
    """Base64 encoded image data."""
