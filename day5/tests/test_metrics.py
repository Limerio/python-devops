"""Unit tests for system metrics."""

from api.metrics import get_system_metrics


def test_metrics_returns_required_fields():
    metrics = get_system_metrics()
    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert "disk_percent" in metrics


def test_metrics_values_in_valid_range():
    metrics = get_system_metrics()
    for key in ("cpu_percent", "memory_percent", "disk_percent"):
        assert 0 <= metrics[key] <= 100


def test_metrics_includes_memory_details():
    metrics = get_system_metrics()
    assert "memory_used_gb" in metrics
    assert "memory_total_gb" in metrics
    assert metrics["memory_total_gb"] >= metrics["memory_used_gb"]
