"""Collect the current source file and its nearby code dependencies."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


IGNORED_DIRS = {"node_modules", ".git", "dist", "build", ".venv", "venv"}
READABLE_EXTENSIONS = {".html", ".wxml", ".js", ".ts", ".json", ".css", ".scss", ".less"}


@dataclass(frozen=True)
class FileContext:
    path: str
    content: str


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _references(content: str, suffix: str) -> Iterable[str]:
    if suffix in {".js", ".ts"}:
        pattern = r"(?:from\s*|import\s*\(|require\s*\()\s*[\"']([^\"']+)[\"']"
        return (match.group(1) for match in re.finditer(pattern, content))
    pattern = r"(?:src|href)\s*=\s*[\"']([^\"']+)[\"']"
    return (match.group(1) for match in re.finditer(pattern, content, re.IGNORECASE))


def _candidate_paths(reference: str, current: Path, root: Path) -> Iterable[Path]:
    reference = reference.split("#", 1)[0].split("?", 1)[0]
    if not reference or reference.startswith(("http:", "https:", "//", "data:")):
        return []
    if reference.startswith("/"):
        base = root / reference.lstrip("/")
    elif reference.startswith("."):
        base = current.parent / reference
    else:
        return []
    candidates = [base]
    if not base.suffix:
        candidates.extend(base.with_suffix(ext) for ext in (".js", ".ts", ".html", ".wxml", ".json"))
        candidates.extend((base / "index").with_suffix(ext) for ext in (".js", ".ts"))
    return candidates


def _sibling_candidates(path: Path) -> Iterable[Path]:
    for extension in (".js", ".ts", ".html", ".wxml"):
        candidate = path.with_suffix(extension)
        if candidate != path:
            yield candidate


def _read_file(path: Path, root: Path) -> str | None:
    if not _inside(path, root) or path.suffix.lower() not in READABLE_EXTENSIONS:
        return None
    if any(part in IGNORED_DIRS for part in path.parts):
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def resolve_context(workspace_root: str, file_path: str, max_chars: int = 24000) -> list[FileContext]:
    root = Path(workspace_root).expanduser().resolve()
    current = Path(file_path).expanduser().resolve()
    if not _inside(current, root):
        raise ValueError("当前文件必须位于 workspace 内")
    if max_chars <= 0:
        raise ValueError("maxContextChars 必须大于 0")

    queue: deque[Path] = deque([current])
    queued = {current}
    discovered: list[Path] = []
    while queue:
        path = queue.popleft()
        if path in discovered:
            continue
        content = _read_file(path, root)
        if content is None:
            continue
        discovered.append(path)
        references = _references(content, path.suffix.lower())
        candidates = list(_sibling_candidates(path))
        for reference in references:
            candidates.extend(_candidate_paths(reference, path, root))
        for candidate in candidates:
            candidate = candidate.resolve()
            if candidate not in queued and _inside(candidate, root):
                queued.add(candidate)
                queue.append(candidate)

    result: list[FileContext] = []
    remaining = max_chars
    for path in discovered:
        content = _read_file(path, root)
        if content is None or remaining <= 0:
            break
        clipped = content[:remaining]
        result.append(FileContext(path=str(path), content=clipped))
        remaining -= len(clipped)
    return result

