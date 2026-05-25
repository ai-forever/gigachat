import pytest
from pydantic import ValidationError

from gigachat.models.files import DeletedFile, File, Image, UploadedFile, UploadedFiles


def test_uploaded_file_creation() -> None:
    data = {
        "id": "file-123",
        "object": "file",
        "bytes": 1024,
        "created_at": 1234567890,
        "filename": "test.txt",
        "purpose": "general",
    }
    file_ = UploadedFile.model_validate(data)
    assert file_.id_ == "file-123"
    assert file_.object_ == "file"
    assert file_.bytes_ == 1024
    assert file_.filename == "test.txt"


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
    data = {"id": "file-1", "deleted": True}
    deleted = DeletedFile.model_validate(data)
    assert deleted.id_ == "file-1"
    assert deleted.deleted is True


def test_image_creation() -> None:
    img = Image(content="base64data")
    assert img.content == "base64data"


def test_file_creation() -> None:
    file_ = File(content="base64data")
    assert file_.content == "base64data"


def test_uploaded_file_validation() -> None:
    with pytest.raises(ValidationError):
        UploadedFile.model_validate({"id": "1"})  # Missing fields
