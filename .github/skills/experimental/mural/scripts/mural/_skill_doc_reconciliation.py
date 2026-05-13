"""SKILL.md reconciliation helpers extracted from the mural facade."""

from __future__ import annotations

import pathlib
import re
from typing import Any

_SKILL_TOOL_TABLE_HEADER_RE = re.compile(
    r"^\|\s*Tool\s*\|\s*Operation\s*\|\s*Description\s*\|\s*$",
    re.IGNORECASE,
)


def _parse_skill_tool_table_impl(text: str) -> list[dict[str, str]]:
    """Parse the ``MCP Tool Reference`` markdown table from SKILL.md text.

    Returns one ``{"name", "operation", "description"}`` mapping per data row.
    The tool name is stripped of surrounding backticks. Returns an empty list
    when the expected header is not found.
    """
    rows: list[dict[str, str]] = []
    lines = text.splitlines()
    header_idx: int | None = None
    for idx, line in enumerate(lines):
        if _SKILL_TOOL_TABLE_HEADER_RE.match(line):
            header_idx = idx
            break
    if header_idx is None:
        return rows
    for line in lines[header_idx + 2 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3:
            continue
        name = cells[0].strip("`").strip()
        if not name.startswith("mural_"):
            break
        rows.append(
            {
                "name": name,
                "operation": cells[1].lower(),
                "description": cells[2],
            }
        )
    return rows


def _validate_skill_md_impl(
    path: pathlib.Path,
    *,
    tool_registry: dict[str, dict[str, Any]],
) -> list[str]:
    """Compare the SKILL.md tool table at ``path`` against ``tool_registry``.

    Returns a list of human-readable diff strings. An empty list means the
    documented surface and the in-process registry agree on tool names and
    operation classification (``read`` vs ``write``). Description prose is
    intentionally not compared because the SKILL.md table uses concise
    user-facing phrasing while ``tool_registry`` carries longer MCP-style
    descriptions.
    """
    diffs: list[str] = []
    text = path.read_text(encoding="utf-8")
    documented = {row["name"]: row for row in _parse_skill_tool_table_impl(text)}
    if not documented:
        diffs.append(f"SKILL.md at {path}: MCP tool reference table not found")
        return diffs
    registered = set(tool_registry.keys())
    documented_names = set(documented.keys())
    for missing in sorted(registered - documented_names):
        diffs.append(f"missing in SKILL.md: {missing}")
    for extra in sorted(documented_names - registered):
        diffs.append(f"extra in SKILL.md (not in _TOOL_REGISTRY): {extra}")
    for name in sorted(registered & documented_names):
        annotations = tool_registry[name].get("annotations", {})
        expected_op = "read" if annotations.get("readOnlyHint") else "write"
        actual_op = documented[name]["operation"]
        if actual_op != expected_op:
            diffs.append(
                f"operation mismatch for {name}: SKILL.md={actual_op!r} "
                f"registry={expected_op!r}"
            )
    return diffs
