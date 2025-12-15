from gigachat.models.assistants import (
    Assistant,
    AssistantDelete,
    AssistantFileDelete,
    Assistants,
    CreateAssistant,
)


def test_assistant_creation() -> None:
    data = {
        "model": "GigaChat",
        "assistant_id": "asst-1",
        "created_at": 1,
        "updated_at": 2,
        "name": "MyAssistant",
    }
    asst = Assistant.model_validate(data)
    assert asst.assistant_id == "asst-1"
    assert asst.model == "GigaChat"
    assert asst.name == "MyAssistant"


def test_assistants_creation() -> None:
    data = {
        "data": [
            {
                "model": "GigaChat",
                "assistant_id": "asst-1",
                "created_at": 1,
                "updated_at": 2,
            }
        ]
    }
    assts = Assistants.model_validate(data)
    assert len(assts.data) == 1
    assert assts.data[0].assistant_id == "asst-1"


def test_create_assistant_creation() -> None:
    data = {"assistant_id": "new-asst", "created_at": 123}
    created = CreateAssistant.model_validate(data)
    assert created.assistant_id == "new-asst"


def test_assistant_delete_creation() -> None:
    data = {"assistant_id": "del-asst", "deleted": True}
    deleted = AssistantDelete.model_validate(data)
    assert deleted.assistant_id == "del-asst"
    assert deleted.deleted is True


def test_assistant_file_delete_creation() -> None:
    data = {"file_id": "file-1", "deleted": True}
    deleted = AssistantFileDelete.model_validate(data)
    assert deleted.file_id == "file-1"
    assert deleted.deleted is True
