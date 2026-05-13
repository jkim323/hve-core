"""MCP stdio server loop extracted from the mural facade."""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Any, Callable

from ._exceptions import FrameTooLarge, MCPInvalidParamsError, MCPProtocolError


def _mcp_handle_message_impl(
    msg: dict[str, Any],
    *,
    executor: concurrent.futures.ThreadPoolExecutor,
    mcp_methods: set[str],
    mcp_handle_initialize: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    client_capabilities: dict[str, Any],
    mcp_list_tools: Callable[[], list[dict[str, Any]]],
    mcp_handle_tools_call: Callable[[dict[str, Any]], dict[str, Any]],
    tool_timeout_secs: float,
    mcp_error_response: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}
    is_notification = "id" not in msg
    # DR-12: full-set membership check before any branching.
    is_known = method in mcp_methods
    if not is_known:
        if is_notification:
            return None
        return mcp_error_response(msg_id, -32601, f"unknown method: {method!r}")
    if method == "initialize":
        if is_notification:
            return None
        result = mcp_handle_initialize(params, client_capabilities)
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        if is_notification:
            return None
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": mcp_list_tools()},
        }
    if method == "tools/call":
        if is_notification:
            return None
        tool_name = params.get("name") if isinstance(params, dict) else None
        future = executor.submit(mcp_handle_tools_call, params)
        try:
            result = future.result(timeout=tool_timeout_secs)
        except concurrent.futures.TimeoutError:
            future.cancel()
            return mcp_error_response(
                msg_id,
                -32000,
                "tool_timeout",
                data={"tool": tool_name, "timeout_secs": tool_timeout_secs},
            )
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    return None


def _run_mcp_stdio_impl(
    stdin: Any,
    stdout: Any,
    *,
    read_frame: Callable[[Any], str | None],
    frame_mcp_message: Callable[[dict[str, Any]], bytes],
    mcp_error_response: Callable[..., dict[str, Any]],
    emit: Callable[[str], None],
    redact: Callable[[str], str],
    parse_mcp_frame: Callable[[str], dict[str, Any] | None],
    mcp_methods: set[str],
    mcp_handle_initialize: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    client_capabilities: dict[str, Any],
    mcp_list_tools: Callable[[], list[dict[str, Any]]],
    mcp_handle_tools_call: Callable[[dict[str, Any]], dict[str, Any]],
    tool_timeout_secs: float,
    exit_success: int,
    exit_failure: int,
) -> int:
    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=1, thread_name_prefix="mural-mcp-tool"
    )
    try:
        while True:
            try:
                line = read_frame(stdin)
            except FrameTooLarge as exc:
                stdout.write(
                    frame_mcp_message(mcp_error_response(None, -32600, str(exc)))
                )
                stdout.flush()
                continue
            except OSError as exc:
                emit(
                    f"mcp stdio read failed: {redact(str(exc))}",
                    level=logging.ERROR,
                )
                return exit_failure
            if not line:
                return exit_success
            try:
                msg = parse_mcp_frame(line)
            except MCPProtocolError as exc:
                stdout.write(
                    frame_mcp_message(mcp_error_response(None, -32700, str(exc)))
                )
                stdout.flush()
                continue
            if msg is None:
                continue
            msg_id = msg.get("id")
            is_notification = "id" not in msg
            try:
                response = _mcp_handle_message_impl(
                    msg,
                    executor=executor,
                    mcp_methods=mcp_methods,
                    mcp_handle_initialize=mcp_handle_initialize,
                    client_capabilities=client_capabilities,
                    mcp_list_tools=mcp_list_tools,
                    mcp_handle_tools_call=mcp_handle_tools_call,
                    tool_timeout_secs=tool_timeout_secs,
                    mcp_error_response=mcp_error_response,
                )
                if response is None:
                    continue
                stdout.write(frame_mcp_message(response))
                stdout.flush()
            except MCPInvalidParamsError as exc:
                if not is_notification:
                    stdout.write(
                        frame_mcp_message(
                            mcp_error_response(
                                msg_id, -32602, exc.message, data={"path": exc.path}
                            )
                        )
                    )
                    stdout.flush()
            except MCPProtocolError as exc:
                if not is_notification:
                    stdout.write(
                        frame_mcp_message(mcp_error_response(msg_id, -32700, str(exc)))
                    )
                    stdout.flush()
            except Exception as exc:  # noqa: BLE001 - boundary
                emit(
                    f"mcp internal error: {redact(repr(exc))}",
                    level=logging.ERROR,
                )
                if not is_notification:
                    stdout.write(
                        frame_mcp_message(
                            mcp_error_response(msg_id, -32603, "internal error")
                        )
                    )
                    stdout.flush()
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
