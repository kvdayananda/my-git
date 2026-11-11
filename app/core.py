"""CodeLens Core Analyzer Engine."""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class FileMetric:
    path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int


def analyze_source_text(filename: str, text: str) -> FileMetric:
    lines = text.splitlines()
    total = len(lines)
    code = 0
    comment = 0
    blank = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank += 1
        elif stripped.startswith(("#", "//", "/*", "*")):
            comment += 1
        else:
            code += 1

    return FileMetric(
        path=filename,
        total_lines=total,
        code_lines=code,
        comment_lines=comment,
        blank_lines=blank,
    )


def summarize_metrics(metrics: List[FileMetric]) -> Dict[str, int]:
    return {
        "files_analyzed": len(metrics),
        "total_lines": sum(m.total_lines for m in metrics),
        "code_lines": sum(m.code_lines for m in metrics),
        "comment_lines": sum(m.comment_lines for m in metrics),
        "blank_lines": sum(m.blank_lines for m in metrics),
    }
