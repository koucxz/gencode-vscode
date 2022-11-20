"""Normalize and validate model output before editor replacement."""

from __future__ import annotations

import re


_FENCE_RE = re.compile(r"^\s*```(?:[a-zA-Z0-9_+-]+)?\s*\n(?P<code>.*?)\n\s*```\s*$", re.DOTALL)
_BAD_PREFIXES = ("i cannot", "i can't", "as an ai", "无法生成", "抱歉")


def normalize_response(text: str, indent: str = "") -> str:
    value = str(text or "").replace("\r\n", "\n").strip()
    fence = _FENCE_RE.match(value)
    if fence:
        value = fence.group("code").strip("\n")
    if not value:
        raise ValueError("模型返回了空代码")
    if value.lower().startswith(_BAD_PREFIXES):
        raise ValueError("模型没有返回可插入代码")
    lines = value.split("\n")
    if indent:
        lines = [indent + line if line.strip() else line for line in lines]
    return "\n".join(lines)

