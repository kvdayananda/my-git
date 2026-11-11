"""Tests for Nexus Telemetry API."""
import pytest
from app.core import MetricRecord, TelemetryRegistry
from app.main import ingest_payload, get_health_status, registry


def setup_function():
    registry._records.clear()


def test_metric_validation():
    valid = MetricRecord("auth-svc", 45.5, 512.0)
    valid.validate()
    assert valid.service_id == "auth-svc"

    with pytest.raises(ValueError):
        MetricRecord("", 10.0, 100.0).validate()

    with pytest.raises(ValueError):
        MetricRecord("svc", 150.0, 100.0).validate()


def test_registry_averaging():
    reg = TelemetryRegistry()
    reg.record_metric(MetricRecord("api", 20.0, 200.0))
    reg.record_metric(MetricRecord("api", 40.0, 220.0))
    reg.record_metric(MetricRecord("worker", 90.0, 1000.0))

    assert reg.compute_average_cpu("api") == 30.0
    assert reg.compute_average_cpu("worker") == 90.0
    assert reg.compute_average_cpu() == 50.0


def test_ingest_and_health():
    res = ingest_payload({"service_id": "gateway", "cpu_percent": 15.0, "memory_mb": 128.0})
    assert res["status"] == "recorded"
    assert res["average_cpu"] == 15.0

    health = get_health_status()
    assert health["status"] == "operational"
    assert health["total_metrics_recorded"] == 1
