import pytest

from gencode_backend.context import FileContext
from gencode_backend.prompt import build_prompt
from gencode_backend.response import normalize_response


def test_prompt_contains_instruction_and_context():
    prompt = build_prompt(
        "typescript",
        "page.ts",
        "create a request helper",
        [FileContext("page.ts", "export const page = true"), FileContext("api.ts", "export const api = 1")],
    )
    assert "create a request helper" in prompt
    assert "page.ts" in prompt and "api.ts" in prompt
    assert "Return only the code" in prompt


def test_response_removes_fence_and_preserves_indent():
    result = normalize_response("```ts\nconst value = 1;\n```", "  ")
    assert result == "  const value = 1;"


def test_response_rejects_empty_or_refusal():
    with pytest.raises(ValueError):
        normalize_response("   ")
    with pytest.raises(ValueError):
        normalize_response("I cannot generate that")

