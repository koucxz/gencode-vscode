"""JSON Lines protocol shared by the VSCode bridge and Python backend."""

from __future__ import annotations

from typing import Any, Dict


def success_response(request_id: str, **payload: Any) -> Dict[str, Any]:
    return {"id": request_id, "ok": True, **payload}


def error_response(request_id: str, error: str) -> Dict[str, Any]:
    return {"id": request_id, "ok": False, "error": error}


def request_id(request: Dict[str, Any]) -> str:
    value = request.get("id")
    return str(value) if value is not None else "unknown"


def validate_request(request: Dict[str, Any]) -> None:
    required = ("action", "language", "filePath", "workspaceRoot", "source")
    missing = [name for name in required if not request.get(name)]
    if missing:
        raise ValueError("缺少请求字段: " + ", ".join(missing))
    if request["action"] != "generate":
        raise ValueError(f"不支持的 action: {request['action']}")

