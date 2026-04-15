from typing import Any, Dict, List

import pytest
from pydantic import BaseModel, Field, ValidationError

from gigachat.models.chat import Chat, Messages, MessagesRole
from gigachat.models.response_format import JsonSchemaResponseFormat

SAMPLE_SCHEMA: Dict[str, Any] = {
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
        JsonSchemaResponseFormat(schema="not a dict")


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
    steps: List[str] = Field(description="Solution steps.")
    final_answer: str = Field(description="The final answer.")


def test_schema_from_basemodel() -> None:
    response_format = JsonSchemaResponseFormat(schema=MathSolution)
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
        JsonSchemaResponseFormat(schema=42)


def test_schema_invalid_class_rejected() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat(schema=int)


def test_dict_schema_passthrough_no_normalization() -> None:
    """Dict schemas are NOT normalized — sent as-is."""
    raw: Dict[str, Any] = {
        "type": "object",
        "properties": {"x": {"type": "string"}},
    }
    response_format = JsonSchemaResponseFormat(schema=raw)
    dumped = response_format.model_dump(exclude_none=True, by_alias=True)
    assert "additionalProperties" not in dumped["schema"]
    assert "required" not in dumped["schema"]
