from typing import Any, Dict, List, Union

import pytest
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from gigachat.models.chat import Chat, Messages, MessagesRole
from gigachat.models.response_format import JsonSchemaResponseFormat, ResponseFormat

SAMPLE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "steps": {"type": "array", "items": {"type": "string"}},
        "final_answer": {"type": "string"},
    },
    "required": ["steps", "final_answer"],
}


def test_json_schema_response_format_creation() -> None:
    rf = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA)
    assert rf.type == "json_schema"
    assert rf.schema_ == SAMPLE_SCHEMA
    assert rf.strict is None


def test_json_schema_response_format_with_strict() -> None:
    rf = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=True)
    assert rf.strict is True


def test_json_schema_response_format_strict_false() -> None:
    rf = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=False)
    assert rf.strict is False


def test_json_schema_response_format_dump_excludes_none_strict() -> None:
    rf = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA)
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    assert "strict" not in dumped
    assert dumped["type"] == "json_schema"
    assert dumped["schema"] == SAMPLE_SCHEMA


def test_json_schema_response_format_dump_includes_strict() -> None:
    rf = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=True)
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    assert dumped["strict"] is True


def test_json_schema_response_format_validate_from_dict() -> None:
    data = {
        "type": "json_schema",
        "schema": SAMPLE_SCHEMA,
        "strict": False,
    }
    rf = JsonSchemaResponseFormat.model_validate(data)
    assert rf.type == "json_schema"
    assert rf.schema_ == SAMPLE_SCHEMA
    assert rf.strict is False


def test_json_schema_response_format_invalid_schema_type() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat(schema="not a dict")


def test_json_schema_response_format_missing_schema() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat.model_validate({"type": "json_schema"})


def test_response_format_public_alias_is_importable() -> None:
    assert ResponseFormat is not None


def test_chat_with_response_format_typed() -> None:
    rf = JsonSchemaResponseFormat(schema=SAMPLE_SCHEMA, strict=False)
    chat = Chat(
        model="GigaChat-2-Max",
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        response_format=rf,
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
# Pydantic BaseModel / TypeAdapter as schema
# ---------------------------------------------------------------------------


class MathSolution(BaseModel):
    steps: List[str] = Field(description="Solution steps.")
    final_answer: str = Field(description="The final answer.")


class CalculateAction(BaseModel):
    action: str = Field(description="Action discriminator.")
    expression: str = Field(description="Math expression to evaluate.")


class FinalAnswerAction(BaseModel):
    action: str = Field(description="Action discriminator.")
    answer: str = Field(description="Final human-readable answer.")


def test_schema_from_basemodel() -> None:
    rf = JsonSchemaResponseFormat(schema=MathSolution)
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    schema = dumped["schema"]
    assert schema["type"] == "object"
    assert "steps" in schema["properties"]
    assert "final_answer" in schema["properties"]
    assert set(schema["required"]) == {"steps", "final_answer"}


def test_schema_from_basemodel_strict() -> None:
    rf = JsonSchemaResponseFormat(schema=MathSolution, strict=True)
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    assert dumped["strict"] is True
    assert dumped["schema"]["type"] == "object"


def test_schema_from_type_adapter_union() -> None:
    adapter: TypeAdapter[Union[int, str]] = TypeAdapter(Union[int, str])
    rf = JsonSchemaResponseFormat(schema=adapter)
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    schema = dumped["schema"]
    assert "anyOf" in schema


def test_schema_from_typing_union() -> None:
    rf = JsonSchemaResponseFormat(schema=TypeAdapter(Union[CalculateAction, FinalAnswerAction]))
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    schema = dumped["schema"]
    assert "anyOf" in schema


def test_schema_from_type_adapter_model() -> None:
    adapter: TypeAdapter[MathSolution] = TypeAdapter(MathSolution)
    rf = JsonSchemaResponseFormat(schema=adapter)
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    schema = dumped["schema"]
    assert schema["type"] == "object"


def test_schema_from_basemodel_in_chat() -> None:
    chat = Chat(
        model="GigaChat-2-Max",
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        response_format=JsonSchemaResponseFormat(schema=MathSolution, strict=False),
    )
    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    rf = dumped["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["schema"]["type"] == "object"
    assert rf["strict"] is False


def test_schema_invalid_type_rejected() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat(schema=42)


def test_schema_invalid_class_rejected() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat(schema=int)


# ---------------------------------------------------------------------------
# Nested models with $defs / $ref
# ---------------------------------------------------------------------------


class Star(BaseModel):
    name: str = Field(description="Name of the star.")


class Galaxy(BaseModel):
    name: str = Field(description="Name of the galaxy.")
    largest_star: Star = Field(description="The largest star.")


class Universe(BaseModel):
    name: str = Field(description="Name of the universe.")
    galaxy: Galaxy = Field(description="A galaxy.")


def test_nested_model_uses_ref() -> None:
    """Nested models use $ref/$defs — no inlining."""
    rf = JsonSchemaResponseFormat(schema=Universe)
    schema = rf.model_dump(exclude_none=True, by_alias=True)["schema"]

    galaxy_prop = schema["properties"]["galaxy"]
    assert "$ref" in galaxy_prop

    assert "$defs" in schema
    assert "Galaxy" in schema["$defs"]
    assert "Star" in schema["$defs"]


def test_dict_schema_passthrough_no_normalization() -> None:
    """Dict schemas are NOT normalized — sent as-is."""
    raw: Dict[str, Any] = {
        "type": "object",
        "properties": {"x": {"type": "string"}},
    }
    rf = JsonSchemaResponseFormat(schema=raw)
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    assert "additionalProperties" not in dumped["schema"]
    assert "required" not in dumped["schema"]


# ---------------------------------------------------------------------------
# Shorthand: Chat(response_format=SomeModel) without wrapping
# ---------------------------------------------------------------------------


class Person(BaseModel):
    name: str = Field(description="Name")
    age: int = Field(description="Age")


def test_chat_response_format_bare_basemodel() -> None:
    """Passing a BaseModel class directly as response_format should work."""
    chat = Chat(
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        response_format=Person,
    )
    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    rf = dumped["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["schema"]["type"] == "object"
    assert "name" in rf["schema"]["properties"]
    assert "age" in rf["schema"]["properties"]


def test_chat_response_format_bare_basemodel_validate() -> None:
    """Chat.model_validate with a bare BaseModel class in response_format."""
    data = {
        "messages": [{"role": "user", "content": "hi"}],
        "response_format": Person,
    }
    chat = Chat.model_validate(data)
    assert chat.response_format is not None
    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    assert dumped["response_format"]["type"] == "json_schema"
    assert dumped["response_format"]["schema"]["type"] == "object"


def test_chat_response_format_bare_type_adapter() -> None:
    """Passing a TypeAdapter directly as response_format should work."""
    adapter: TypeAdapter[Union[int, str]] = TypeAdapter(Union[int, str])
    chat = Chat(
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        response_format=adapter,
    )
    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    rf = dumped["response_format"]
    assert rf["type"] == "json_schema"
    assert "anyOf" in rf["schema"]


def test_chat_response_format_bare_nested_model() -> None:
    """Nested BaseModel as response_format uses $ref/$defs."""
    chat = Chat(
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        response_format=Universe,
    )
    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    rf = dumped["response_format"]
    assert rf["type"] == "json_schema"
    schema = rf["schema"]
    assert "$defs" in schema
    assert "Galaxy" in schema["$defs"]
