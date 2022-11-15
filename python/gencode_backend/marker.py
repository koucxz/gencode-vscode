"""Locate genCode(\"...\") calls and describe their replacement range."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)
class Marker:
    start: int
    end: int
    instruction: str
    indent: str
    raw: str


_DOUBLE_QUOTED = re.compile(r'\bgenCode\s*\(\s*"((?:\\.|[^"\\])*)"\s*\)', re.IGNORECASE)
_SINGLE_QUOTED = re.compile(r"\bgenCode\s*\(\s*'((?:\\.|[^'\\])*)'\s*\)", re.IGNORECASE)


def _indent_at(source: str, offset: int) -> str:
    line_start = source.rfind("\n", 0, offset) + 1
    prefix = source[line_start:offset]
    return prefix[: len(prefix) - len(prefix.lstrip(" \t"))]


def _instruction(quote: str, value: str) -> str:
    try:
        parsed = ast.literal_eval(quote + value + quote)
    except (SyntaxError, ValueError):
        parsed = value
    return str(parsed).strip()


def find_markers(source: str) -> list[Marker]:
    markers: list[Marker] = []
    for pattern, quote in ((_DOUBLE_QUOTED, '"'), (_SINGLE_QUOTED, "'")):
        for match in pattern.finditer(source):
            markers.append(
                Marker(
                    start=match.start(),
                    end=match.end(),
                    instruction=_instruction(quote, match.group(1)),
                    indent=_indent_at(source, match.start()),
                    raw=match.group(0),
                )
            )
    return sorted(markers, key=lambda marker: marker.start)


def find_marker(source: str, cursor_offset: int) -> Optional[Marker]:
    markers = find_markers(source)
    if not markers:
        return None
    for marker in markers:
        if marker.start <= cursor_offset <= marker.end:
            return marker
    line_start = source.rfind("\n", 0, cursor_offset) + 1
    line_end = source.find("\n", cursor_offset)
    if line_end < 0:
        line_end = len(source)
    for marker in markers:
        if marker.start >= line_start and marker.end <= line_end:
            return marker
    return min(markers, key=lambda marker: abs(marker.start - cursor_offset))

