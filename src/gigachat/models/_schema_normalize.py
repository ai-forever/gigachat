"""JSON Schema normalization for Pydantic-generated schemas.

Applied automatically when a user passes a Pydantic BaseModel or TypeAdapter
as ``schema`` in ``JsonSchemaResponseFormat``.  Dict schemas are sent as-is
(passthrough mode).

The normalization adds ``additionalProperties: false`` on every object schema
(unless already set) to help the model avoid generating extra fields.
"""

from __future__ import annotations

import inspect
from typing import Any

import pydantic


def to_strict_json_schema(
    model: type[pydantic.BaseModel] | pydantic.TypeAdapter[Any],
) -> dict[str, Any]:
    """Generate and normalize a JSON Schema from a Pydantic model / TypeAdapter."""
    if inspect.isclass(model) and issubclass(model, pydantic.BaseModel):
        schema = model.model_json_schema()
    elif isinstance(model, pydantic.TypeAdapter):
        schema = model.json_schema()
    else:
        raise TypeError(f"Expected a pydantic.BaseModel subclass or pydantic.TypeAdapter, got {type(model)}")

    _add_additional_properties_false(schema)
    return schema


def _add_additional_properties_false(schema: Any) -> None:
    """Recursively add ``additionalProperties: false`` to all object schemas."""
    if not isinstance(schema, dict):
        return

    if schema.get("type") == "object" and "additionalProperties" not in schema:
        schema["additionalProperties"] = False

    _recurse_subschemas(schema)


def _recurse_subschemas(schema: dict[str, Any]) -> None:
    """Visit all nested sub-schemas and apply normalization."""
    for key in ("properties", "$defs", "definitions"):
        sub = schema.get(key)
        if isinstance(sub, dict):
            for v in sub.values():
                _add_additional_properties_false(v)

    for key in ("items", "additionalProperties"):
        sub = schema.get(key)
        if isinstance(sub, dict):
            _add_additional_properties_false(sub)

    for key in ("anyOf", "oneOf", "allOf"):
        sub = schema.get(key)
        if isinstance(sub, list):
            for item in sub:
                _add_additional_properties_false(item)
