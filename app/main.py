"""CodeLens Main Entry Point."""
from app.core import FileMetric, analyze_source_text, summarize_metrics


class CodeLensApp:
    def __init__(self) -> None:
        self.metrics: list[FileMetric] = []

    def scan_file(self, filename: str, content: str) -> FileMetric:
        metric = analyze_source_text(filename, content)
        self.metrics.append(metric)
        return metric

    def get_report(self) -> dict:
        summary = summarize_metrics(self.metrics)
        hotspots = [m.path for m in self.metrics if m.code_lines > 200]
        return {
            "summary": summary,
            "hotspots": hotspots,
            "status": "ready",
        }
