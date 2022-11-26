from gencode_backend.marker import find_marker, find_markers


def test_parses_html_comment_and_instruction():
    source = '<div>\n  genCode("create a form")\n</div>'
    marker = find_marker(source, source.index("genCode") + 3)
    assert marker is not None
    assert marker.instruction == "create a form"
    assert source[marker.start : marker.end] == 'genCode("create a form")'
    assert marker.indent == "  "


def test_parses_js_line_and_bare_markers():
    source = "const a = genCode(\"add fetch helper\")\nconst b = genCode('add a button')\n"
    markers = find_markers(source)
    assert [marker.instruction for marker in markers] == ["add fetch helper", "add a button"]
    assert find_marker(source, source.index("genCode", 3) + 1).instruction == "add fetch helper"


def test_cursor_on_line_selects_marker():
    source = 'const a = 1\nconst b = genCode("create a button")\nconst c = 2\n'
    marker = find_marker(source, source.index("genCode") + 2)
    assert marker is not None
    assert marker.raw == 'genCode("create a button")'


def test_decodes_escaped_quotes():
    marker = find_markers('const a = genCode("say \\"hello\\"")')[0]
    assert marker.instruction == 'say "hello"'

