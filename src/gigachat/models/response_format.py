import inspect
from typing import Any, Dict, Literal, Optional, Union

import pydantic
from pydantic import BaseModel, Field, model_validator


class JsonSchemaResponseFormat(BaseModel):
    """Response format requesting JSON output conforming to a JSON Schema.

    .. note:: **Beta.** This feature may not work correctly with all model versions.

    ``schema`` accepts:

    * ``dict``  -- raw JSON Schema, sent as-is (passthrough).
    * ``type[pydantic.BaseModel]``  -- auto-converted via
      ``model_json_schema()``.
    """

    type: Literal["json_schema"] = Field(default="json_schema", description="Response format type.")
    schema_: Dict[str, Any] = Field(alias="schema", description="JSON Schema that the response must conform to.")
    strict: Optional[bool] = Field(default=None, description="Request strict schema adherence (best-effort).")

    @model_validator(mode="before")
    @classmethod
    def _validate_and_convert_schema(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        schema = values.get("schema")
        if schema is None:
            return values

        # Pydantic BaseModel subclass -> generate JSON Schema
        if inspect.isclass(schema) and issubclass(schema, pydantic.BaseModel):
            values = dict(values)
            values["schema"] = schema.model_json_schema()
            return values

        # Plain dict -> passthrough
        if isinstance(schema, dict):
            return values

        raise ValueError(f"'schema' must be a dict or a pydantic.BaseModel subclass; got {type(schema).__name__}")


ResponseFormat = Union[JsonSchemaResponseFormat, Dict[str, Any]]
"""Accepted types for ``Chat.response_format``:

* ``JsonSchemaResponseFormat`` — fully typed object.
* ``dict`` — raw JSON passed through as-is.
"""
