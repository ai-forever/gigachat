from typing import Any, Literal

import pytest
from pydantic import BaseModel, Field, ValidationError

from gigachat.models.chat import Chat, Messages, MessagesRole
from gigachat.models.chat_completions import ChatResponseFormat
from gigachat.models.response_format import JsonSchemaResponseFormat

SAMPLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "steps": {"type": "array", "items": {"type": "string"}},
        "final_answer": {"type": "string"},
    },
    "required": ["steps", "final_answer"],
}


def test_json_schema_response_format_creation() -> None:
    response_format = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA)
    assert response_format.type == "json_schema"
    assert response_format.schema_ == SAMPLE_SCHEMA
    assert response_format.strict is None


def test_json_schema_response_format_with_strict() -> None:
    response_format = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=True)
    assert response_format.strict is True


def test_json_schema_response_format_strict_false() -> None:
    response_format = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=False)
    assert response_format.strict is False


def test_json_schema_response_format_dump_excludes_none_strict() -> None:
    response_format = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA)
    dumped = response_format.model_dump(exclude_none=True, by_alias=True)
    assert "strict" not in dumped
    assert dumped["type"] == "json_schema"
    assert dumped["schema"] == SAMPLE_SCHEMA


def test_json_schema_response_format_dump_includes_strict() -> None:
    response_format = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=True)
    dumped = response_format.model_dump(exclude_none=True, by_alias=True)
    assert dumped["strict"] is True


def test_json_schema_response_format_validate_from_dict() -> None:
    data = {
        "type": "json_schema",
        "schema": SAMPLE_SCHEMA,
        "strict": False,
    }
    response_format = JsonSchemaResponseFormat.model_validate(data)
    assert response_format.type == "json_schema"
    assert response_format.schema_ == SAMPLE_SCHEMA
    assert response_format.strict is False


def test_json_schema_response_format_invalid_schema_type() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat.model_validate({"schema": "not a dict"})


def test_json_schema_response_format_missing_schema() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat.model_validate({"type": "json_schema"})


def test_chat_with_response_format_typed() -> None:
    response_format = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=False)
    chat = Chat(
        model="GigaChat-2-Max",
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        response_format=response_format,
    )
    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    assert "response_format" in dumped
    assert dumped["response_format"]["type"] == "json_schema"
    assert dumped["response_format"]["schema"] == SAMPLE_SCHEMA
    assert dumped["response_format"]["strict"] is False


def test_chat_with_response_format_dict() -> None:
    rf_dict = {
        "type": "json_schema",
        "schema": SAMPLE_SCHEMA,
        "strict": True,
    }
    chat = Chat(
        model="GigaChat-2-Max",
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        response_format=rf_dict,
    )
    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    assert dumped["response_format"]["type"] == "json_schema"
    assert dumped["response_format"]["schema"] == SAMPLE_SCHEMA


def test_chat_without_response_format() -> None:
    chat = Chat(
        messages=[Messages(role=MessagesRole.USER, content="hi")],
    )
    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    assert "response_format" not in dumped


def test_chat_validate_response_format_from_dict() -> None:
    data = {
        "model": "GigaChat-2-Max",
        "messages": [{"role": "user", "content": "hi"}],
        "response_format": {
            "type": "json_schema",
            "schema": SAMPLE_SCHEMA,
        },
    }
    chat = Chat.model_validate(data)
    assert chat.response_format is not None


# ---------------------------------------------------------------------------
# Pydantic BaseModel as schema
# ---------------------------------------------------------------------------


class MathSolution(BaseModel):
    steps: list[str] = Field(description="Solution steps.")
    final_answer: str = Field(description="The final answer.")


def test_schema_from_basemodel() -> None:
    response_format = JsonSchemaResponseFormat(schema=MathSolution)
    assert response_format.schema_ == MathSolution.model_json_schema()
    dumped = response_format.model_dump(exclude_none=True, by_alias=True)
    schema = dumped["schema"]
    assert schema["type"] == "object"
    assert "steps" in schema["properties"]
    assert "final_answer" in schema["properties"]
    assert set(schema["required"]) == {"steps", "final_answer"}


def test_schema_from_basemodel_strict() -> None:
    response_format = JsonSchemaResponseFormat(schema=MathSolution, strict=True)
    dumped = response_format.model_dump(exclude_none=True, by_alias=True)
    assert dumped["strict"] is True
    assert dumped["schema"]["type"] == "object"


def test_schema_from_basemodel_in_chat() -> None:
    chat = Chat(
        model="GigaChat-2-Max",
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        response_format=JsonSchemaResponseFormat(schema=MathSolution, strict=False),
    )
    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    response_format = dumped["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["schema"]["type"] == "object"
    assert response_format["strict"] is False


def test_schema_invalid_type_rejected() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat.model_validate({"schema": 42})


def test_schema_invalid_class_rejected() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat.model_validate({"schema": int})


def test_dict_schema_passthrough_no_normalization() -> None:
    """Dict schemas are NOT normalized — sent as-is."""
    raw: dict[str, Any] = {
        "type": "object",
        "properties": {"x": {"type": "string"}},
    }
    response_format = JsonSchemaResponseFormat(schema=raw)
    dumped = response_format.model_dump(exclude_none=True, by_alias=True)
    assert "additionalProperties" not in dumped["schema"]
    assert "required" not in dumped["schema"]


@pytest.mark.parametrize("schema", [MathSolution, MathSolution(steps=["1 + 1"], final_answer="2")])
def test_primary_schema_from_basemodel(schema: type[BaseModel] | BaseModel) -> None:
    response_format = ChatResponseFormat(type="json_schema", schema=schema)
    expected = MathSolution.model_json_schema()
    assert response_format.schema_ == expected
    assert response_format.model_dump(by_alias=True) == {
        "type": "json_schema",
        "schema": expected,
        "strict": None,
        "regex": None,
    }


@pytest.mark.parametrize("schema", [SAMPLE_SCHEMA, "raw schema", None])
def test_primary_schema_passthrough(schema: dict[str, Any] | str | None) -> None:
    response_format = ChatResponseFormat(type="json_schema", schema=schema)
    assert response_format.schema_ == schema
    assert response_format.model_dump(by_alias=True)["schema"] == schema


def test_legacy_schema_instance_rejected() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat.model_validate({"schema": MathSolution(steps=[], final_answer="2")})


@pytest.mark.parametrize("mode", ["validation", "serialization"])
def test_response_format_json_schema(mode: Literal["validation", "serialization"]) -> None:
    legacy = JsonSchemaResponseFormat.model_json_schema(mode=mode)
    assert legacy["properties"]["schema"] == {
        "additionalProperties": True,
        "description": "JSON Schema that the response must conform to.",
        "title": "Schema",
        "type": "object",
    }
    assert legacy["required"] == ["schema"]
    assert "$defs" not in legacy

    primary = ChatResponseFormat.model_json_schema(mode=mode)
    assert primary["properties"]["schema"] == {
        "anyOf": [{"additionalProperties": True, "type": "object"}, {"type": "string"}, {"type": "null"}],
        "default": None,
        "description": "JSON Schema or raw schema payload.",
        "title": "Schema",
    }
    assert "required" not in primary
    assert "$defs" not in primary
