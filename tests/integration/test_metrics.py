from backend.core.metrics import get_metrics, REQUEST_COUNT, REQUEST_DURATIONS


class TestMetrics:
    def test_get_metrics_empty(self):
        metrics = get_metrics()
        assert metrics["request_count"] >= 0
        assert isinstance(metrics["average_duration_ms"], float)
        assert isinstance(metrics["total_duration_seconds"], float)

    def test_get_metrics_accumulated(self):
        REQUEST_DURATIONS.append(0.1)
        REQUEST_DURATIONS.append(0.2)
        metrics = get_metrics()
        assert metrics["request_count"] >= 0
        assert metrics["average_duration_ms"] > 0
        REQUEST_DURATIONS.clear()
