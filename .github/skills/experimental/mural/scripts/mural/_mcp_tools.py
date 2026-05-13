"""MCP tool list and dispatch helpers extracted from the mural facade."""

from __future__ import annotations

import json
from typing import Any, Callable

from ._exceptions import (
    MCPInvalidParamsError,
    MuralAmbiguousWorkspaceError,
    MuralAPIError,
    MuralAuthScopeError,
    MuralSecurityError,
    MuralValidationError,
)


def _mcp_list_tools_impl(
    tool_registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for name, spec in tool_registry.items():
        entry: dict[str, Any] = {
            "name": name,
            "title": spec["title"],
            "description": spec["description"],
            "inputSchema": spec["input_schema"],
        }
        annotations = spec.get("annotations")
        if annotations:
            entry["annotations"] = annotations
        tools.append(entry)
    return tools


def _mcp_tool_error_payload_impl(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, MuralAPIError):
        return {
            "error": exc.code,
            "message": exc.message,
            "request_id": exc.request_id,
            "status": exc.status,
        }
    if isinstance(exc, MuralAmbiguousWorkspaceError):
        return {
            "error": "ambiguous_workspace",
            "message": str(exc),
            "workspace_ids": list(exc.workspace_ids),
        }
    if isinstance(exc, MuralAuthScopeError):
        return {
            "error": "auth_scope_required",
            "message": str(exc),
            "required_scope": exc.scope,
            "granted_scopes": list(exc.granted),
        }
    if isinstance(exc, MuralSecurityError):
        return {"error": "security_error", "message": str(exc)}
    return {"error": "validation_error", "message": str(exc)}


def _mcp_handle_tools_call_impl(
    params: dict[str, Any],
    *,
    tool_registry: dict[str, dict[str, Any]],
    validate_tool_input_schema: Callable[[dict[str, Any], Any, str], None],
    require_scope: Callable[[list[str]], None],
    idempotency_get: Callable[[str, str], Any],
    maybe_elicit: Callable[[str, dict[str, Any]], bool],
    idempotency_put: Callable[[str, str, dict[str, Any]], None],
) -> dict[str, Any]:
    if not isinstance(params, dict):
        raise MCPInvalidParamsError("params must be an object")
    name = params.get("name")
    if not isinstance(name, str) or not name:
        raise MCPInvalidParamsError("name is required", path="$.name")
    spec = tool_registry.get(name)
    if spec is None:
        raise MCPInvalidParamsError(f"unknown tool {name!r}", path="$.name")
    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise MCPInvalidParamsError("arguments must be an object", path="$.arguments")
    validate_tool_input_schema(spec["input_schema"], arguments, "$.arguments")
    dry_run = bool(arguments.pop("dry_run", False))
    idempotency_key = arguments.pop("idempotency_key", None)
    is_destructive = bool(spec.get("destructive"))
    creates = bool(spec.get("creates"))
    if dry_run and is_destructive:
        preview = {
            "dry_run": True,
            "tool": name,
            "arguments": dict(arguments),
        }
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(preview, ensure_ascii=False, sort_keys=True),
                }
            ],
            "isError": False,
        }
    if is_destructive:
        required_scopes = spec.get("required_scopes") or ["murals:write"]
        try:
            require_scope(required_scopes)
        except MuralAuthScopeError as exc:
            payload = _mcp_tool_error_payload_impl(exc)
            return {
                "content": [
                    {"type": "text", "text": json.dumps(payload, ensure_ascii=False)}
                ],
                "isError": True,
            }
    if creates and isinstance(idempotency_key, str) and idempotency_key:
        cached = idempotency_get(name, idempotency_key)
        if cached is not None:
            return cached
    if is_destructive and not maybe_elicit(name, arguments):
        payload = {
            "error": "elicitation_declined",
            "message": "user declined elicitation for destructive tool",
            "tool": name,
        }
        return {
            "content": [
                {"type": "text", "text": json.dumps(payload, ensure_ascii=False)}
            ],
            "isError": True,
        }
    try:
        result = spec["handler"](arguments)
    except (
        MuralAPIError,
        MuralSecurityError,
        MuralAmbiguousWorkspaceError,
        MuralAuthScopeError,
        MuralValidationError,
    ) as exc:
        payload = _mcp_tool_error_payload_impl(exc)
        return {
            "content": [
                {"type": "text", "text": json.dumps(payload, ensure_ascii=False)}
            ],
            "isError": True,
        }
    text = json.dumps(result, default=str, ensure_ascii=False)
    response = {
        "content": [{"type": "text", "text": text}],
        "isError": False,
    }
    if creates and isinstance(idempotency_key, str) and idempotency_key:
        idempotency_put(name, idempotency_key, response)
    return response
