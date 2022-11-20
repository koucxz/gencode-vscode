"""Prompt construction for code generation."""

from __future__ import annotations

from typing import Sequence

from .context import FileContext


def build_prompt(
    language: str,
    file_path: str,
    instruction: str,
    contexts: Sequence[FileContext],
) -> str:
    context_blocks = []
    for index, item in enumerate(contexts):
        label = "CURRENT FILE" if index == 0 else "RELATED FILE"
        context_blocks.append(f"[{label}] {item.path}\n```\n{item.content}\n```")
    joined = "\n\n".join(context_blocks)
    request = instruction or "根据当前代码上下文补全 genCode 标记。"
    return (
        "You are a careful software engineer generating production-ready code.\n"
        f"Target language: {language}\n"
        f"Target file: {file_path}\n"
        f"User request: {request}\n\n"
        "Use the current file and related files below as the source of truth. "
        "Preserve existing naming, imports, framework conventions, and indentation. "
        "Return only the code that should replace the genCode marker. Do not include "
        "Markdown fences, explanations, or a leading/trailing commentary.\n\n"
        f"{joined}"
    )

