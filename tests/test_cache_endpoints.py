"""
Tests for the cache endpoints.

This module contains tests for the cache API endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """
    Test client fixture.

    Returns:
        TestClient: FastAPI test client
    """
    return TestClient(app)


@pytest.fixture
def mock_cache():
    """
    Mock cache fixture.

    This creates a mock TranslationCache that doesn't actually cache anything.
    """
    with patch("src.api.endpoints.translation_cache") as mock_cache:
        # Set up mock cache stats
        mock_cache.get_stats.return_value = {
            "size": 10,
            "max_size": 1000,
            "ttl": 3600,
            "hits": 50,
            "misses": 20,
            "hit_rate": 0.714,
        }

        yield mock_cache


def test_cache_stats_endpoint(client, mock_cache):
    """
    Test cache stats endpoint.
    """
    response = client.get("/cache/stats")

    assert response.status_code == 200
    data = response.json()

    # Check response
    assert data["size"] == 10
    assert data["max_size"] == 1000
    assert data["ttl"] == 3600
    assert data["hits"] == 50
    assert data["misses"] == 20
    assert data["hit_rate"] == 0.714

    # Check that get_stats was called
    mock_cache.get_stats.assert_called_once()


def test_clear_cache_endpoint(client, mock_cache):
    """
    Test clear cache endpoint.
    """
    response = client.post("/cache/clear")

    assert response.status_code == 200
    data = response.json()

    # Check response
    assert data["status"] == "ok"
    assert data["message"] == "Cache cleared"

    # Check that clear was called
    mock_cache.clear.assert_called_once()
