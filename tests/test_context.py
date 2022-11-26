from pathlib import Path

from gencode_backend.context import resolve_context


def test_resolves_imports_scripts_and_sibling_files(tmp_path: Path):
    (tmp_path / "page.ts").write_text("import { api } from './api'\n", encoding="utf-8")
    (tmp_path / "api.ts").write_text("export const api = () => 1\n", encoding="utf-8")
    (tmp_path / "page.wxml").write_text("<script src='./page.js'></script>", encoding="utf-8")
    (tmp_path / "page.js").write_text("export default {}", encoding="utf-8")
    contexts = resolve_context(str(tmp_path), str(tmp_path / "page.ts"), 10000)
    paths = {Path(item.path).name for item in contexts}
    assert {"page.ts", "api.ts", "page.js"}.issubset(paths)


def test_ignores_workspace_escape_and_limits_size(tmp_path: Path):
    outside = tmp_path.parent / "outside.ts"
    outside.write_text("secret", encoding="utf-8")
    (tmp_path / "main.ts").write_text("import '../outside'\n" + "x" * 100, encoding="utf-8")
    contexts = resolve_context(str(tmp_path), str(tmp_path / "main.ts"), 20)
    assert all(Path(item.path).is_relative_to(tmp_path) for item in contexts)
    assert sum(len(item.content) for item in contexts) <= 20


def test_skips_ignored_directories(tmp_path: Path):
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "dep.ts").write_text("export const dep = 1", encoding="utf-8")
    (tmp_path / "main.ts").write_text("import 'dep'", encoding="utf-8")
    contexts = resolve_context(str(tmp_path), str(tmp_path / "main.ts"), 1000)
    assert all("node_modules" not in item.path for item in contexts)

