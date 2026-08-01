import base64
from pathlib import Path

import pytest
from pydantic import ValidationError

from gigachat.models.files import DeletedFile, DownloadedFile, Image, UploadedFile, UploadedFiles


def test_uploaded_file_creation() -> None:
    data = {
        "id": "file-123",
        "object": "file",
        "bytes": 1024,
        "created_at": 1234567890,
        "filename": "test.txt",
        "purpose": "general",
        "access_policy": "private",
        "modalities": ["text"],
    }
    file_ = UploadedFile.model_validate(data)
    assert file_.id_ == "file-123"
    assert file_.id == "file-123"
    assert file_.object_ == "file"
    assert file_.bytes_ == 1024
    assert file_.filename == "test.txt"
    assert file_.modalities == ["text"]


def test_uploaded_files_creation() -> None:
    data = {
        "data": [
            {
                "id": "file-1",
                "object": "file",
                "bytes": 100,
                "created_at": 123,
                "filename": "a.txt",
                "purpose": "general",
            }
        ]
    }
    files = UploadedFiles.model_validate(data)
    assert len(files.data) == 1
    assert files.data[0].id_ == "file-1"


def test_deleted_file_creation() -> None:
    data = {"id": "file-1", "deleted": True, "access_policy": "private"}
    deleted = DeletedFile.model_validate(data)
    assert deleted.id_ == "file-1"
    assert deleted.deleted is True
    assert deleted.access_policy == "private"


def test_image_creation() -> None:
    img = Image(content="base64data")
    assert img.content == "base64data"


def test_image_decodes_and_saves_base64_content(tmp_path: Path) -> None:
    raw_content = b"\xff\xd8\xffjpeg-content"
    image = Image(content=base64.b64encode(raw_content).decode("ascii"))

    output = image.save(tmp_path / "generated.jpg")

    assert image.to_bytes() == raw_content
    assert output == tmp_path / "generated.jpg"
    assert output.read_bytes() == raw_content


def test_downloaded_file_saves_raw_content(tmp_path: Path) -> None:
    downloaded = DownloadedFile(content=b"binary-content", content_type="application/octet-stream")

    output = downloaded.save(str(tmp_path / "download.bin"))

    assert output == tmp_path / "download.bin"
    assert output.read_bytes() == b"binary-content"


def test_uploaded_file_validation() -> None:
    with pytest.raises(ValidationError):
        UploadedFile.model_validate({"id": "1"})  # Missing fields
