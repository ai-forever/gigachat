from enum import Enum
from typing import Any, Dict, List, Optional, Union

import pytest
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from gigachat.models._schema_normalize import to_strict_json_schema
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
# A+ tests: Pydantic BaseModel / TypeAdapter as schema
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
    assert schema["additionalProperties"] is False
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
    rf = JsonSchemaResponseFormat(schema=Union[CalculateAction, FinalAnswerAction])
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    schema = dumped["schema"]
    assert "anyOf" in schema


def test_schema_from_type_adapter_model() -> None:
    adapter: TypeAdapter[MathSolution] = TypeAdapter(MathSolution)
    rf = JsonSchemaResponseFormat(schema=adapter)
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    schema = dumped["schema"]
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False


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
    assert rf["schema"]["additionalProperties"] is False
    assert rf["strict"] is False


def test_schema_invalid_type_rejected() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat(schema=42)


def test_schema_invalid_class_rejected() -> None:
    with pytest.raises(ValidationError):
        JsonSchemaResponseFormat(schema=int)


# ---------------------------------------------------------------------------
# A+ tests: nested models with $defs / $ref handling
# ---------------------------------------------------------------------------


class Star(BaseModel):
    name: str = Field(description="Name of the star.")


class Galaxy(BaseModel):
    name: str = Field(description="Name of the galaxy.")
    largest_star: Star = Field(description="The largest star.")


class Universe(BaseModel):
    name: str = Field(description="Name of the universe.")
    galaxy: Galaxy = Field(description="A galaxy.")


def test_nested_model_ref_with_sibling_is_inlined() -> None:
    """$ref with sibling keys (e.g. description) must be inlined."""
    rf = JsonSchemaResponseFormat(schema=Universe)
    schema = rf.model_dump(exclude_none=True, by_alias=True)["schema"]

    galaxy_prop = schema["properties"]["galaxy"]
    assert "$ref" not in galaxy_prop, "$ref with sibling 'description' should be inlined"
    assert galaxy_prop["type"] == "object"
    assert "description" in galaxy_prop

    star_prop = galaxy_prop["properties"]["largest_star"]
    assert "$ref" not in star_prop
    assert star_prop["type"] == "object"


def test_nested_model_additional_properties_false() -> None:
    schema = to_strict_json_schema(Universe)
    assert schema["additionalProperties"] is False

    galaxy_prop = schema["properties"]["galaxy"]
    assert galaxy_prop["additionalProperties"] is False

    star_prop = galaxy_prop["properties"]["largest_star"]
    assert star_prop["additionalProperties"] is False


def test_nested_model_required_set() -> None:
    schema = to_strict_json_schema(Universe)
    assert set(schema["required"]) == {"name", "galaxy"}
    assert set(schema["properties"]["galaxy"]["required"]) == {"name", "largest_star"}


# ---------------------------------------------------------------------------
# A+ tests: normalization details
# ---------------------------------------------------------------------------


class Color(str, Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class ColorInfo(BaseModel):
    color: Color = Field(description="The detected color")
    hex_code: str


def test_enum_field_ref_with_sibling_is_inlined() -> None:
    """$ref with sibling keys (description from Field) should be inlined."""
    schema = to_strict_json_schema(ColorInfo)
    color_prop = schema["properties"]["color"]
    assert "$ref" not in color_prop, "$ref should be inlined when description sibling exists"
    assert "enum" in color_prop


class SimpleColorInfo(BaseModel):
    color: Color
    hex_code: str


def test_bare_ref_without_siblings_preserved() -> None:
    """Bare $ref (no sibling keys) is kept as-is."""
    schema = to_strict_json_schema(SimpleColorInfo)
    color_prop = schema["properties"]["color"]
    assert "$ref" in color_prop


class ItemWrapper(BaseModel):
    items_list: List[Star]


def test_array_of_models_normalized() -> None:
    schema = to_strict_json_schema(ItemWrapper)
    items_prop = schema["properties"]["items_list"]
    assert items_prop["type"] == "array"


class OptionalField(BaseModel):
    name: str
    note: Optional[str] = None


def test_optional_field_default_none_stripped() -> None:
    schema = to_strict_json_schema(OptionalField)
    note_prop = schema["properties"]["note"]
    assert "default" not in note_prop


class SingleAllOf(BaseModel):
    tag: str


def test_single_allof_flattened() -> None:
    """allOf with a single entry should be flattened into the parent."""
    raw_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "data": {
                "allOf": [{"type": "string"}],
                "description": "A value",
            }
        },
    }
    rf = JsonSchemaResponseFormat(schema=raw_schema)
    dumped = rf.model_dump(exclude_none=True, by_alias=True)
    assert dumped["schema"] == raw_schema


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
    assert rf["schema"]["additionalProperties"] is False


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
    """Nested BaseModel as response_format is normalized correctly."""
    chat = Chat(
        messages=[Messages(role=MessagesRole.USER, content="hi")],
        response_format=Universe,
    )
    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    rf = dumped["response_format"]
    assert rf["type"] == "json_schema"
    schema = rf["schema"]
    assert schema["additionalProperties"] is False
    galaxy_prop = schema["properties"]["galaxy"]
    assert galaxy_prop["type"] == "object"
    assert galaxy_prop["additionalProperties"] is False
