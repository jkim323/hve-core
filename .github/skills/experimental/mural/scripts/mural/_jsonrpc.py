"""MCP JSON-RPC framing helpers for the Mural package.

Carved from ``mural.__init__`` per the modularization plan. Helpers stay
pure and accept façade-owned state explicitly so ``import mural`` keeps the
same monkeypatch and shared-state behavior through re-exported symbols.
"""

from __future__ import annotations

import json
from typing import Any

from ._constants import MURAL_MAX_FRAME_BYTES
from ._exceptions import FrameTooLarge, MCPInvalidParamsError, MCPProtocolError

_MCP_PROTOCOL_PREFERRED = "2025-11-25"
_MCP_PROTOCOL_FALLBACK = "2025-06-18"
_MCP_SERVER_INFO = {"name": "mural", "version": "1.0.0"}
_MCP_CAPABILITIES: dict[str, Any] = {"tools": {"listChanged": False}}
_MCP_METHODS: frozenset[str] = frozenset(
    {
        "initialize",
        "notifications/initialized",
        "tools/list",
        "tools/call",
    }
)


def _frame_mcp_message(obj: dict[str, Any]) -> bytes:
    """Encode ``obj`` as a single newline-delimited JSON frame."""
    return (json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _parse_mcp_frame(line: bytes) -> dict[str, Any] | None:
    """Decode one NDJSON line into a JSON-RPC message; ``None`` for blank lines."""
    try:
        text = line.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MCPProtocolError(f"frame is not valid utf-8: {exc}") from exc
    text = text.strip()
    if not text:
        return None
    try:
        msg = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MCPProtocolError(f"invalid json frame: {exc}") from exc
    if not isinstance(msg, dict):
        raise MCPProtocolError("frame must be a JSON object")
    return msg


def _read_frame(stream: Any, limit: int = MURAL_MAX_FRAME_BYTES) -> bytes | None:
    """Read one NDJSON frame from ``stream`` enforcing ``limit`` bytes.

    Returns the raw line including its trailing newline, an empty bytes
    object on EOF (so callers can mirror the existing ``readline()`` EOF
    semantics), or raises ``FrameTooLarge`` if the frame exceeds ``limit``.
    Reads in fixed-size chunks via ``readline`` so a hostile producer cannot
    pin the entire process on a single oversized line.
    """
    chunk_size = 65536
    pieces: list[bytes] = []
    total = 0
    while True:
        chunk = stream.readline(chunk_size)
        if not chunk:
            break
        pieces.append(chunk)
        total += len(chunk)
        if total > limit:
            while not chunk.endswith(b"\n"):
                chunk = stream.readline(chunk_size)
                if not chunk:
                    break
            raise FrameTooLarge(f"mcp frame exceeds {limit} bytes")
        if chunk.endswith(b"\n"):
            break
    if not pieces:
        return b""
    return b"".join(pieces)


def _mcp_error_response(
    msg_id: Any,
    code: int,
    message: str,
    data: Any = None,
) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": msg_id, "error": err}


def _mcp_handle_initialize(
    params: dict[str, Any],
    client_capabilities: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(params, dict):
        raise MCPInvalidParamsError("params must be an object")
    requested = params.get("protocolVersion")
    if requested == _MCP_PROTOCOL_PREFERRED:
        chosen = _MCP_PROTOCOL_PREFERRED
    elif requested == _MCP_PROTOCOL_FALLBACK or requested is None:
        chosen = _MCP_PROTOCOL_FALLBACK
    else:
        raise MCPInvalidParamsError(
            f"unsupported protocolVersion {requested!r}",
            path="$.protocolVersion",
        )
    caps = params.get("capabilities")
    client_capabilities.clear()
    if isinstance(caps, dict):
        client_capabilities.update(caps)
    return {
        "protocolVersion": chosen,
        "capabilities": _MCP_CAPABILITIES,
        "serverInfo": _MCP_SERVER_INFO,
    }
