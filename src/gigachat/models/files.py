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
    modalities: Optional[List[str]] = Field(default=None, description="Automatically detected file modalities.")

    @property
    def id(self) -> str:
        """Return the file identifier using the documented attribute name."""
        return self.id_


class UploadedFiles(APIResponse):
    """List of uploaded files."""

    data: List[UploadedFile] = Field(description="List of file objects.")


class DeletedFile(APIResponse):
    """Information about a deleted file."""

    id_: str = Field(alias="id", description="File identifier.")
    deleted: bool = Field(description="Deletion status. True if deleted.")
    access_policy: Optional[str] = Field(default=None, description="Access policy.")


class Image(APIResponse):
    """Image content."""

    content: str = Field(description="Base64 encoded image data.")


class DownloadedFile(APIResponse):
    """Raw content downloaded from an uploaded file."""

    content: bytes = Field(description="Raw file content.")
    content_type: Optional[str] = Field(default=None, description="Response media type.")
    content_disposition: Optional[str] = Field(default=None, description="Response content disposition.")
