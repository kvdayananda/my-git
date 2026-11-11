"""Main Application Entry Point."""
from app.core import MetricRecord, TelemetryRegistry

registry = TelemetryRegistry()


def ingest_payload(data: dict) -> dict:
    rec = MetricRecord(
        service_id=data["service_id"],
        cpu_percent=float(data["cpu_percent"]),
        memory_mb=float(data["memory_mb"]),
        status=data.get("status", "healthy"),
    )
    registry.record_metric(rec)
    return {
        "status": "recorded",
        "service_id": rec.service_id,
        "average_cpu": registry.compute_average_cpu(rec.service_id),
    }


def get_health_status() -> dict:
    return {
        "status": "operational",
        "total_metrics_recorded": registry.total_count(),
        "overall_average_cpu": registry.compute_average_cpu(),
    }
