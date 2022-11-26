import pytest

from gencode_backend import __main__ as backend
from gencode_backend.protocol import validate_request


def test_protocol_rejects_missing_fields():
    with pytest.raises(ValueError):
        validate_request({"action": "generate"})


def test_process_line_returns_error_json_for_invalid_payload():
    response = backend.process_line('{"id":"x","action":"unknown"}')
    assert response["id"] == "x"
    assert response["ok"] is False


def test_handle_request_uses_marker_and_returns_offsets(monkeypatch, tmp_path):
    source = 'const value = genCode("add value")\n'
    file_path = tmp_path / "page.ts"
    file_path.write_text(source, encoding="utf-8")
    from gencode_backend import llm

    monkeypatch.setattr(llm, "generate_code", lambda *args, **kwargs: "const value = 1;")
    response = backend.handle_request(
        {
            "id": "1",
            "action": "generate",
            "language": "typescript",
            "filePath": str(file_path),
            "workspaceRoot": str(tmp_path),
            "source": source,
            "cursorOffset": source.index("genCode"),
            "config": {"maxContextChars": 1000},
        }
    )
    assert response["ok"] is True
    assert response["code"].startswith("const value")
    assert response["markerStart"] < response["markerEnd"]

