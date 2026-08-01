from gigachat.models.models import Model


def test_model_parses_documented_capability_type() -> None:
    model = Model.model_validate(
        {
            "id": "GigaChat-2-Max",
            "object": "model",
            "owned_by": "salutedevices",
            "type": "chat",
        }
    )

    assert model.type == "chat"
    assert model.model_dump(by_alias=True)["type"] == "chat"
