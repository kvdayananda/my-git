"""Nexus Telemetry Core Engine."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class MetricRecord:
    service_id: str
    cpu_percent: float
    memory_mb: float
    status: str = "healthy"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def validate(self) -> None:
        if not self.service_id or not self.service_id.strip():
            raise ValueError("service_id must be a non-empty string.")
        if not (0.0 <= self.cpu_percent <= 100.0):
            raise ValueError(f"cpu_percent must be between 0 and 100, got {self.cpu_percent}")
        if self.memory_mb < 0:
            raise ValueError("memory_mb must be non-negative.")


class TelemetryRegistry:
    def __init__(self) -> None:
        self._records: list[MetricRecord] = []

    def record_metric(self, metric: MetricRecord) -> MetricRecord:
        metric.validate()
        self._records.append(metric)
        return metric

    def get_service_metrics(self, service_id: str) -> list[MetricRecord]:
        return [r for r in self._records if r.service_id == service_id]

    def compute_average_cpu(self, service_id: Optional[str] = None) -> float:
        matching = [r.cpu_percent for r in self._records if service_id is None or r.service_id == service_id]
        if not matching:
            return 0.0
        return round(sum(matching) / len(matching), 2)

    def total_count(self) -> int:
        return len(self._records)
