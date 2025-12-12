from typing import List, Optional

from pydantic import Field

from gigachat.models.base import APIResponse


class UploadedFile(APIResponse):
    """Information about an uploaded file."""

    id_: str = Field(alias="id", description="File identifier.")
    object_: str = Field(alias="object", description="Object type.")
    bytes_: int = Field(alias="bytes", description="File size in bytes.")
    created_at: int = Field(description="Creation timestamp (Unix time).")
    filename: str = Field(description="Name of the file.")
    purpose: str = Field(description="Intended purpose of the file.")
    access_policy: Optional[str] = Field(default=None, description="Access policy.")


class UploadedFiles(APIResponse):
    """List of uploaded files."""

    data: List[UploadedFile] = Field(description="List of file objects.")


class DeletedFile(APIResponse):
    """Information about a deleted file."""

    id_: str = Field(alias="id", description="File identifier.")
    deleted: bool = Field(description="Deletion status. True if deleted.")


class Image(APIResponse):
    """Image content."""

    content: str = Field(description="Base64 encoded image data.")
