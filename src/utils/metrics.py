"""
Prometheus metrics for the Translation Service.

This module provides Prometheus metrics for monitoring the Translation Service.
"""

from prometheus_client import Counter, Gauge, Histogram, Summary

# Request metrics
REQUEST_COUNT = Counter(
    "translation_request_total",
    "Total number of translation requests",
    ["endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "translation_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 30.0, 60.0),
)

# Translation metrics
TRANSLATION_COUNT = Counter(
    "translation_count_total",
    "Total number of translations",
    ["source_lang", "target_lang", "status"],
)

TRANSLATION_LATENCY = Histogram(
    "translation_latency_seconds",
    "Translation latency in seconds",
    ["source_lang", "target_lang"],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 30.0, 60.0),
)

TRANSLATION_TEXT_LENGTH = Histogram(
    "translation_text_length",
    "Length of translated text",
    ["source_lang", "target_lang"],
    buckets=(10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000),
)

# Model metrics
MODEL_LOAD_TIME = Summary(
    "translation_model_load_time_seconds",
    "Time to load the translation model",
    ["model_size", "device", "compute_type"],
)

MODEL_MEMORY_USAGE = Gauge(
    "translation_model_memory_usage_bytes",
    "Memory usage of the translation model",
    ["model_size", "device", "compute_type"],
)

# System metrics
SYSTEM_MEMORY_USAGE = Gauge(
    "translation_system_memory_usage_bytes",
    "System memory usage",
    ["type"],  # total, used, free
)

SYSTEM_CPU_USAGE = Gauge(
    "translation_system_cpu_usage_percent",
    "System CPU usage",
    ["type"],  # user, system, idle
)

# Task metrics
TASK_COUNT = Counter(
    "translation_task_total",
    "Total number of async translation tasks",
    ["task_type", "status"],
)

TASK_LATENCY = Histogram(
    "translation_task_latency_seconds",
    "Task latency in seconds",
    ["task_type"],
    buckets=(
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
        15.0,
        30.0,
        60.0,
        120.0,
        300.0,
        600.0,
    ),
)

TASK_QUEUE_SIZE = Gauge(
    "translation_task_queue_size",
    "Number of tasks in the queue",
    ["status"],  # pending, processing, completed, failed
)
