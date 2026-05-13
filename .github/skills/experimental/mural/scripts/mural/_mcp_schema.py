"""MCP tool input schema helpers extracted from the mural facade."""

from __future__ import annotations

import re
from typing import Any

from ._exceptions import MCPInvalidParamsError


def _matches_json_type(value: Any, allowed: tuple[str, ...]) -> bool:
    for name in allowed:
        if name == "null":
            if value is None:
                return True
        elif name == "boolean":
            if isinstance(value, bool):
                return True
        elif name == "integer":
            if isinstance(value, int) and not isinstance(value, bool):
                return True
        elif name == "number":
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return True
        elif name == "string":
            if isinstance(value, str):
                return True
        elif name == "array":
            if isinstance(value, list):
                return True
        elif name == "object":
            if isinstance(value, dict):
                return True
    return False


def _validate_tool_input_schema(
    schema: dict[str, Any], value: Any, path: str = "$"
) -> None:
    """Minimal JSON Schema validator covering the subset used by tool registry.

    Raises :class:`MCPInvalidParamsError` on the first violation.
    """
    if "type" in schema:
        types = schema["type"]
        if isinstance(types, str):
            allowed = (types,)
        elif isinstance(types, list):
            allowed = tuple(types)
        else:
            raise MCPInvalidParamsError(
                f"{path}: schema 'type' must be string or list, "
                f"got {type(types).__name__}",
                path=path,
            )
        if not _matches_json_type(value, allowed):
            raise MCPInvalidParamsError(
                f"{path}: expected type {list(allowed)}, got {type(value).__name__}",
                path=path,
            )
    if "enum" in schema and value not in schema["enum"]:
        raise MCPInvalidParamsError(
            f"{path}: value not in enum {schema['enum']!r}", path=path
        )
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise MCPInvalidParamsError(
                f"{path}: string shorter than minLength {schema['minLength']}",
                path=path,
            )
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise MCPInvalidParamsError(
                f"{path}: string longer than maxLength {schema['maxLength']}",
                path=path,
            )
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise MCPInvalidParamsError(
                f"{path}: string does not match pattern {schema['pattern']!r}",
                path=path,
            )
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise MCPInvalidParamsError(
                f"{path}: value less than minimum {schema['minimum']}", path=path
            )
        if "maximum" in schema and value > schema["maximum"]:
            raise MCPInvalidParamsError(
                f"{path}: value greater than maximum {schema['maximum']}", path=path
            )
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise MCPInvalidParamsError(
                f"{path}: array shorter than minItems {schema['minItems']}", path=path
            )
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise MCPInvalidParamsError(
                f"{path}: array longer than maxItems {schema['maxItems']}", path=path
            )
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_tool_input_schema(item_schema, item, f"{path}[{index}]")
    if isinstance(value, dict):
        properties = schema.get("properties") or {}
        required = schema.get("required") or []
        for key in required:
            if key not in value:
                raise MCPInvalidParamsError(
                    f"{path}: missing required property {key!r}",
                    path=f"{path}.{key}",
                )
        additional = schema.get("additionalProperties", True)
        for key, sub in value.items():
            if key in properties:
                _validate_tool_input_schema(properties[key], sub, f"{path}.{key}")
            elif additional is False:
                raise MCPInvalidParamsError(
                    f"{path}: unexpected property {key!r}",
                    path=f"{path}.{key}",
                )


def _validate_tool_registry(tool_registry: dict[str, dict[str, Any]]) -> None:
    """Validate every MCP tool registry entry at module load time."""
    for name, entry in tool_registry.items():
        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            raise RuntimeError(
                f"tool_registry[{name!r}].title must be a non-empty string"
            )
        desc = entry.get("description")
        if not isinstance(desc, str) or not desc:
            raise RuntimeError(
                f"tool_registry[{name!r}].description must be a non-empty string"
            )
        parts = desc.split("\n\n", 1)
        if len(parts) != 2:
            raise RuntimeError(
                f"tool_registry[{name!r}].description must contain a blank-line "
                "separator between summary and details"
            )
        summary, details = parts
        if not summary or "\n" in summary:
            raise RuntimeError(
                f"tool_registry[{name!r}].description summary must be a single "
                "non-empty line"
            )
        if len(summary) > 120:
            raise RuntimeError(
                f"tool_registry[{name!r}].description summary exceeds 120 chars "
                f"({len(summary)})"
            )
        if not details.strip():
            raise RuntimeError(
                f"tool_registry[{name!r}].description details must be non-empty"
            )
        schema = entry.get("input_schema")
        if not isinstance(schema, dict):
            raise RuntimeError(f"tool_registry[{name!r}].input_schema must be a dict")
        if schema.get("type") != "object":
            raise RuntimeError(
                f"tool_registry[{name!r}].input_schema.type must be 'object'"
            )
        if schema.get("additionalProperties") is not False:
            raise RuntimeError(
                f"tool_registry[{name!r}].input_schema.additionalProperties "
                "must be False"
            )
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise RuntimeError(
                f"tool_registry[{name!r}].input_schema.properties must be a dict"
            )
        required = schema.get("required")
        if required is not None:
            if not isinstance(required, list) or not all(
                isinstance(required_name, str) for required_name in required
            ):
                raise RuntimeError(
                    f"tool_registry[{name!r}].input_schema.required must be a "
                    "list of strings"
                )
            unknown = [
                required_name
                for required_name in required
                if required_name not in properties
            ]
            if unknown:
                raise RuntimeError(
                    f"tool_registry[{name!r}].input_schema.required references "
                    f"undeclared properties: {unknown}"
                )
        if not callable(entry.get("handler")):
            raise RuntimeError(f"tool_registry[{name!r}].handler must be callable")
        if not isinstance(entry.get("annotations"), dict):
            raise RuntimeError(
                f"tool_registry[{name!r}].annotations must be a dict"
            )
