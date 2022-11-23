"""Line-oriented process entry point for the VSCode extension."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict

from .protocol import error_response, request_id, success_response, validate_request


def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle one protocol request.

    Imports are intentionally local so protocol validation remains usable even
    when optional LangChain dependencies have not been installed yet.
    """
    validate_request(request)
    from .context import resolve_context
    from .llm import generate_code
    from .marker import find_marker
    from .prompt import build_prompt
    from .response import normalize_response

    source = str(request["source"])
    cursor_offset = int(request.get("cursorOffset", len(source)))
    marker = find_marker(source, cursor_offset)
    if marker is None:
        raise ValueError('当前光标附近没有找到 genCode("...") 调用')

    config = request.get("config") or {}
    max_context_chars = int(config.get("maxContextChars", 24000))
    contexts = resolve_context(
        workspace_root=request["workspaceRoot"],
        file_path=request["filePath"],
        max_chars=max_context_chars,
    )
    prompt = build_prompt(
        language=request["language"],
        file_path=request["filePath"],
        instruction=marker.instruction,
        contexts=contexts,
    )
    generated = generate_code(
        prompt,
        model_name=str(config.get("model") or "text-davinci-003"),
        base_url=str(config.get("baseUrl") or "") or None,
    )
    code = normalize_response(generated, marker.indent)
    return success_response(
        request_id(request),
        code=code,
        markerStart=marker.start,
        markerEnd=marker.end,
        contextFiles=[item.path for item in contexts],
    )


def process_line(line: str) -> Dict[str, Any]:
    try:
        request = json.loads(line)
        if not isinstance(request, dict):
            raise ValueError("请求必须是 JSON 对象")
        return handle_request(request)
    except Exception as exc:  # noqa: BLE001 - protocol must always return JSON.
        request = locals().get("request", {})
        return error_response(request_id(request), str(exc))


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        response = process_line(line)
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

