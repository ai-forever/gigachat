import builtins
import inspect
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic.json_schema import SkipJsonSchema


class JsonSchemaResponseFormat(BaseModel):
    """Response format requesting JSON output conforming to a JSON Schema.

    .. note:: **Beta.** This feature may not work correctly with all model versions.

    ``schema`` accepts:

    * ``dict``  -- raw JSON Schema, sent as-is (passthrough).
    * ``type[pydantic.BaseModel]``  -- auto-converted via
      ``model_json_schema()``.
    """

    type: Literal["json_schema"] = Field(default="json_schema", description="Response format type.")
    schema_: dict[str, Any] = Field(alias="schema", description="JSON Schema that the response must conform to.")
    strict: bool | None = Field(default=None, description="Request strict schema adherence (best-effort).")

    @field_validator(
        "schema_", mode="before", json_schema_input_type=dict[str, Any] | SkipJsonSchema[builtins.type[BaseModel]]
    )
    @classmethod
    def _validate_and_convert_schema(cls, schema: object) -> object:
        if schema is None:
            return schema

        # Pydantic BaseModel subclass -> generate JSON Schema
        if inspect.isclass(schema) and issubclass(schema, BaseModel):
            return schema.model_json_schema()

        # Plain dict -> passthrough
        if isinstance(schema, dict):
            return schema

        raise ValueError(f"'schema' must be a dict or a pydantic.BaseModel subclass; got {type(schema).__name__}")


ResponseFormat = JsonSchemaResponseFormat | dict[str, Any]
"""Accepted types for ``Chat.response_format``:

* ``JsonSchemaResponseFormat`` — fully typed object.
* ``dict`` — raw JSON passed through as-is.
"""
