import base64
from pathlib import Path
from typing import List, Literal, Optional, Union

from pydantic import Field

from gigachat.models.base import APIResponse


class UploadedFile(APIResponse):
    """Information about an uploaded file."""

    id_: str = Field(alias="id", description="File identifier.")
    object_: str = Field(alias="object", description="Object type.")
    bytes_: int = Field(alias="bytes", description="File size in bytes.")
    created_at: int = Field(description="Creation timestamp (Unix time).")
    filename: str = Field(description="Name of the file.")
    purpose: Literal["general", "assistant"] = Field(description="Intended purpose of the file.")
    access_policy: Literal["public", "private"] = Field(default="private", description="Access policy.")
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

    def to_bytes(self) -> bytes:
        """Decode and return the image content."""
        return base64.b64decode(self.content, validate=True)

    def save(self, path: Union[str, Path]) -> Path:
        """Decode and save the image content."""
        output_path = Path(path)
        output_path.write_bytes(self.to_bytes())
        return output_path


class DownloadedFile(APIResponse):
    """Raw content downloaded from an uploaded file."""

    content: bytes = Field(description="Raw file content.")
    content_type: Optional[str] = Field(default=None, description="Response media type.")
    content_disposition: Optional[str] = Field(default=None, description="Response content disposition.")

    def save(self, path: Union[str, Path]) -> Path:
        """Save the raw file content."""
        output_path = Path(path)
        output_path.write_bytes(self.content)
        return output_path
