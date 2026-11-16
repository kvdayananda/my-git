"""Tests for CodeLens Inspector."""
from app.core import analyze_source_text, summarize_metrics
from app.main import CodeLensApp


def test_analyze_source():
    code = """# File header
def add(a, b):
    # Perform sum
    return a + b

"""
    m = analyze_source_text("calc.py", code)
    assert m.total_lines == 5
    assert m.comment_lines == 2
    assert m.blank_lines == 1
    assert m.code_lines == 2


def test_summarize_metrics():
    app = CodeLensApp()
    app.scan_file("a.py", "x = 1\ny = 2")
    app.scan_file("b.py", "# Comment\n\nz = 3")
    report = app.get_report()

    assert report["summary"]["files_analyzed"] == 2
    assert report["summary"]["code_lines"] == 3
    assert report["summary"]["comment_lines"] == 1
    assert report["summary"]["blank_lines"] == 1
