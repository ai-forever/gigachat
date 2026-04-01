"""JSON Schema normalization for Pydantic-generated schemas.

Applied automatically when a user passes a Pydantic BaseModel or TypeAdapter
as ``schema`` in ``JsonSchemaResponseFormat``.  Dict schemas are sent as-is
(passthrough mode).

The normalization ensures the generated schema is compatible with server-side
``response_format=json_schema`` enforcement:

* ``additionalProperties: false`` on every object schema (unless already set)
* ``required`` is set to all ``properties`` keys (strict mode requires every property)
* single-entry ``allOf`` is flattened
* ``$ref`` with sibling keywords is inlined (resolved from root)
* ``default: None`` is stripped (the schema is still nullable via ``anyOf``)
"""

from __future__ import annotations

import copy
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

    schema = copy.deepcopy(schema)
    return _ensure_strict_json_schema(schema, path=(), root=schema)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ensure_strict_json_schema(
    json_schema: object,
    *,
    path: tuple[str, ...],
    root: dict[str, object],
) -> dict[str, Any]:
    """Recursively mutate *json_schema* to conform to the strict standard."""
    if not isinstance(json_schema, dict):
        raise TypeError(f"Expected dict, got {type(json_schema)}; path={path}")

    _normalize_defs(json_schema, path=path, root=root)
    _normalize_object(json_schema, path=path, root=root)
    _normalize_items(json_schema, path=path, root=root)
    _normalize_any_of(json_schema, path=path, root=root)
    _normalize_all_of(json_schema, path=path, root=root)
    _strip_none_default(json_schema)

    return _maybe_inline_ref(json_schema, path=path, root=root)


def _normalize_defs(schema: dict[str, Any], *, path: tuple[str, ...], root: dict[str, object]) -> None:
    for key in ("$defs", "definitions"):
        defs = schema.get(key)
        if isinstance(defs, dict):
            for name, sub in defs.items():
                _ensure_strict_json_schema(sub, path=(*path, key, name), root=root)


def _normalize_object(schema: dict[str, Any], *, path: tuple[str, ...], root: dict[str, object]) -> None:
    if schema.get("type") == "object" and "additionalProperties" not in schema:
        schema["additionalProperties"] = False

    properties = schema.get("properties")
    if isinstance(properties, dict):
        schema["required"] = list(properties.keys())
        schema["properties"] = {
            k: _ensure_strict_json_schema(v, path=(*path, "properties", k), root=root) for k, v in properties.items()
        }


def _normalize_items(schema: dict[str, Any], *, path: tuple[str, ...], root: dict[str, object]) -> None:
    items = schema.get("items")
    if isinstance(items, dict):
        schema["items"] = _ensure_strict_json_schema(items, path=(*path, "items"), root=root)


def _normalize_any_of(schema: dict[str, Any], *, path: tuple[str, ...], root: dict[str, object]) -> None:
    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        schema["anyOf"] = [
            _ensure_strict_json_schema(v, path=(*path, "anyOf", str(i)), root=root) for i, v in enumerate(any_of)
        ]


def _normalize_all_of(schema: dict[str, Any], *, path: tuple[str, ...], root: dict[str, object]) -> None:
    all_of = schema.get("allOf")
    if not isinstance(all_of, list):
        return
    if len(all_of) == 1:
        schema.update(_ensure_strict_json_schema(all_of[0], path=(*path, "allOf", "0"), root=root))
        schema.pop("allOf")
    else:
        schema["allOf"] = [
            _ensure_strict_json_schema(e, path=(*path, "allOf", str(i)), root=root) for i, e in enumerate(all_of)
        ]


def _strip_none_default(schema: dict[str, Any]) -> None:
    if "default" in schema and schema["default"] is None:
        schema.pop("default")


def _maybe_inline_ref(
    schema: dict[str, Any],
    *,
    path: tuple[str, ...],
    root: dict[str, object],
) -> dict[str, Any]:
    ref = schema.get("$ref")
    if ref and _has_more_than_n_keys(schema, 1):
        if not isinstance(ref, str):
            raise TypeError(f"Expected $ref to be a string, got {type(ref)}")

        resolved = _resolve_ref(root=root, ref=ref)
        if not isinstance(resolved, dict):
            raise ValueError(f"$ref {ref!r} resolved to non-dict: {resolved!r}")

        schema.update({**resolved, **schema})
        schema.pop("$ref")
        return _ensure_strict_json_schema(schema, path=path, root=root)

    return schema


def _resolve_ref(*, root: dict[str, object], ref: str) -> object:
    """Resolve a JSON Pointer ``#/...`` against *root*."""
    if not ref.startswith("#/"):
        raise ValueError(f"Unsupported $ref format {ref!r}; must start with #/")

    parts = ref[2:].split("/")
    current: object = root
    for part in parts:
        if not isinstance(current, dict):
            raise ValueError(f"Non-dict while resolving {ref!r}: {current!r}")
        current = current[part]
    return current


def _has_more_than_n_keys(d: dict[str, object], n: int) -> bool:
    i = 0
    for _ in d:
        i += 1
        if i > n:
            return True
    return False
