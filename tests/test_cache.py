"""
Tests for the translation cache.

This module contains tests for the translation cache implementation.
"""

import time
from unittest.mock import patch

import pytest

from src.utils.cache import TranslationCache, generate_cache_key


@pytest.fixture
def cache():
    """Create a translation cache for testing."""
    return TranslationCache(max_size=5, ttl=10)


def test_cache_get_set(cache):
    """Test basic cache get and set operations."""
    # Set a value
    cache.set("key1", "value1")

    # Get the value
    value = cache.get("key1")
    assert value == "value1"

    # Get a non-existent key
    value = cache.get("key2")
    assert value is None


def test_cache_ttl(cache):
    """Test cache time-to-live functionality."""
    # Set a value
    cache.set("key1", "value1")

    # Get the value immediately
    value = cache.get("key1")
    assert value == "value1"

    # Mock time.time to return a future time
    with patch("time.time", return_value=time.time() + 20):
        # Get the value after TTL has expired
        value = cache.get("key1")
        assert value is None


def test_cache_max_size(cache):
    """Test cache max size functionality."""
    # Fill the cache to max size
    for i in range(5):
        cache.set(f"key{i}", f"value{i}")

    # Verify all values are in the cache
    for i in range(5):
        assert cache.get(f"key{i}") == f"value{i}"

    # Add one more item, which should evict the oldest
    cache.set("key5", "value5")

    # The oldest item should be evicted
    assert cache.get("key0") is None

    # The newest items should still be in the cache
    for i in range(1, 6):
        assert cache.get(f"key{i}") == f"value{i}"


def test_cache_clear(cache):
    """Test cache clear functionality."""
    # Set some values
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    # Clear the cache
    cache.clear()

    # Verify the cache is empty
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_cache_stats(cache):
    """Test cache statistics."""
    # Set some values
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    # Get some values (hits)
    cache.get("key1")
    cache.get("key2")

    # Get a non-existent key (miss)
    cache.get("key3")

    # Get stats
    stats = cache.get_stats()

    # Verify stats
    assert stats["size"] == 2
    assert stats["max_size"] == 5
    assert stats["ttl"] == 10
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 2 / 3


def test_generate_cache_key():
    """Test generate_cache_key function."""
    key = generate_cache_key(
        text="Hello",
        source_lang="en",
        target_lang="fr",
        beam_size=5,
        max_length=200,
    )

    assert key == "en:fr:5:200:Hello"

    # Test with different parameters
    key2 = generate_cache_key(
        text="Hello",
        source_lang="es",
        target_lang="de",
        beam_size=10,
        max_length=100,
    )

    assert key2 == "es:de:10:100:Hello"
