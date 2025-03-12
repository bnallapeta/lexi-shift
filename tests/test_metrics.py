"""
Tests for the Prometheus metrics.

This module contains tests for the Prometheus metrics implementation.
"""

from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import REGISTRY

from src.utils.metrics import (
    MODEL_LOAD_TIME,
    MODEL_MEMORY_USAGE,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    SYSTEM_CPU_USAGE,
    SYSTEM_MEMORY_USAGE,
    TASK_COUNT,
    TASK_LATENCY,
    TASK_QUEUE_SIZE,
    TRANSLATION_COUNT,
    TRANSLATION_LATENCY,
    TRANSLATION_TEXT_LENGTH,
)


def test_request_metrics():
    """Test request metrics."""
    # Record some metrics
    REQUEST_COUNT.labels(endpoint="/translate", status=200).inc()
    REQUEST_COUNT.labels(endpoint="/translate", status=500).inc()
    REQUEST_COUNT.labels(endpoint="/batch_translate", status=200).inc()

    REQUEST_LATENCY.labels(endpoint="/translate").observe(0.5)
    REQUEST_LATENCY.labels(endpoint="/batch_translate").observe(1.0)

    # Get sample value
    sample_value = REGISTRY.get_sample_value(
        "translation_request_total", {"endpoint": "/translate", "status": "200"}
    )

    # Check that metrics were recorded
    assert sample_value is not None
    assert sample_value > 0


def test_translation_metrics():
    """Test translation metrics."""
    # Record some metrics
    TRANSLATION_COUNT.labels(source_lang="en", target_lang="fr", status="success").inc()
    TRANSLATION_COUNT.labels(source_lang="en", target_lang="fr", status="error").inc()
    TRANSLATION_COUNT.labels(source_lang="es", target_lang="en", status="success").inc()

    TRANSLATION_LATENCY.labels(source_lang="en", target_lang="fr").observe(0.5)
    TRANSLATION_LATENCY.labels(source_lang="es", target_lang="en").observe(1.0)

    TRANSLATION_TEXT_LENGTH.labels(source_lang="en", target_lang="fr").observe(100)
    TRANSLATION_TEXT_LENGTH.labels(source_lang="es", target_lang="en").observe(200)

    # Get sample value
    sample_value = REGISTRY.get_sample_value(
        "translation_count_total",
        {"source_lang": "en", "target_lang": "fr", "status": "success"},
    )

    # Check that metrics were recorded
    assert sample_value is not None
    assert sample_value > 0


def test_model_metrics():
    """Test model metrics."""
    # Record some metrics
    MODEL_LOAD_TIME.labels(model_size="small", device="cpu", compute_type="float32").observe(5.0)
    MODEL_MEMORY_USAGE.labels(model_size="small", device="cpu", compute_type="float32").set(
        1000000000
    )

    # Get sample value
    sample_value = REGISTRY.get_sample_value(
        "translation_model_load_time_seconds_sum",
        {"model_size": "small", "device": "cpu", "compute_type": "float32"},
    )

    # Check that metrics were recorded
    assert sample_value is not None
    assert sample_value > 0


def test_system_metrics():
    """Test system metrics."""
    # Record some metrics
    SYSTEM_MEMORY_USAGE.labels(type="total").set(8000000000)
    SYSTEM_MEMORY_USAGE.labels(type="used").set(4000000000)
    SYSTEM_MEMORY_USAGE.labels(type="free").set(4000000000)

    SYSTEM_CPU_USAGE.labels(type="user").set(50.0)
    SYSTEM_CPU_USAGE.labels(type="system").set(20.0)
    SYSTEM_CPU_USAGE.labels(type="idle").set(30.0)

    # Get sample value
    sample_value = REGISTRY.get_sample_value(
        "translation_system_memory_usage_bytes", {"type": "total"}
    )

    # Check that metrics were recorded
    assert sample_value is not None
    assert sample_value > 0


def test_task_metrics():
    """Test task metrics."""
    # Record some metrics
    TASK_COUNT.labels(task_type="translate", status="pending").inc()
    TASK_COUNT.labels(task_type="translate", status="processing").inc()
    TASK_COUNT.labels(task_type="translate", status="completed").inc()
    TASK_COUNT.labels(task_type="translate", status="failed").inc()

    TASK_LATENCY.labels(task_type="translate").observe(5.0)
    TASK_LATENCY.labels(task_type="batch_translate").observe(10.0)

    TASK_QUEUE_SIZE.labels(status="pending").set(5)
    TASK_QUEUE_SIZE.labels(status="processing").set(2)
    TASK_QUEUE_SIZE.labels(status="completed").set(10)
    TASK_QUEUE_SIZE.labels(status="failed").set(1)

    # Get sample value
    sample_value = REGISTRY.get_sample_value(
        "translation_task_total", {"task_type": "translate", "status": "completed"}
    )

    # Check that metrics were recorded
    assert sample_value is not None
    assert sample_value > 0
