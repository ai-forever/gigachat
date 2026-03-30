from __future__ import annotations

import inspect
from typing import Any, Literal, get_origin

import pydantic
from pydantic import BaseModel, Field, model_validator

from gigachat.models._schema_normalize import to_strict_json_schema


class JsonSchemaResponseFormat(BaseModel):
    """Response format requesting JSON output conforming to a JSON Schema.

    ``schema`` accepts:

    * ``dict``  -- raw JSON Schema, sent as-is (passthrough).
    * ``type[pydantic.BaseModel]``  -- auto-converted via
      ``model_json_schema()`` and normalized (OpenAI-style).
    * ``pydantic.TypeAdapter``  -- auto-converted via ``.json_schema()``
      and normalized (OpenAI-style).
    * supported typing annotations such as ``Union[Foo, Bar]`` --
      auto-converted through ``pydantic.TypeAdapter`` and normalized.
    """

    type: Literal["json_schema"] = Field(default="json_schema", description="Response format type.")
    schema_: dict[str, Any] = Field(alias="schema", description="JSON Schema that the response must conform to.")
    strict: bool | None = Field(default=None, description="Request strict schema adherence (best-effort).")

    @model_validator(mode="before")
    @classmethod
    def _validate_and_convert_schema(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        schema = values.get("schema")
        if schema is None:
            return values

        # Pydantic BaseModel subclass -> generate + normalize
        if inspect.isclass(schema) and issubclass(schema, pydantic.BaseModel):
            values = dict(values)
            values["schema"] = to_strict_json_schema(schema)
            return values

        # Pydantic TypeAdapter -> generate + normalize
        if isinstance(schema, pydantic.TypeAdapter):
            values = dict(values)
            values["schema"] = to_strict_json_schema(schema)
            return values

        # Supported typing annotation (e.g. Union[Foo, Bar]) -> TypeAdapter
        if get_origin(schema) is not None:
            values = dict(values)
            values["schema"] = to_strict_json_schema(pydantic.TypeAdapter(schema))
            return values

        # Plain dict -> passthrough (no normalization)
        if isinstance(schema, dict):
            return values

        raise ValueError(
            f"'schema' must be a dict, a pydantic.BaseModel subclass, "
            f"a supported typing annotation, or a pydantic.TypeAdapter; "
            f"got {type(schema).__name__}"
        )


ResponseFormat = JsonSchemaResponseFormat | dict[str, Any] | type[pydantic.BaseModel] | Any
"""Accepted types for ``Chat.response_format``:

* ``JsonSchemaResponseFormat`` — fully typed object.
* ``dict`` — raw JSON passed through as-is.
* ``type[BaseModel]`` — Pydantic model class (auto-converted to JSON Schema).
* ``TypeAdapter`` — Pydantic TypeAdapter (auto-converted to JSON Schema).
"""
