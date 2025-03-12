"""
Tests for the language detection endpoint.

This module contains tests for the language detection API endpoint.
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
def mock_model():
    """
    Mock model fixture.

    This creates a mock TranslationModel that doesn't actually load any models.
    """
    with patch("src.models.translation.TranslationModel", autospec=True) as mock_cls:
        # Create a mock instance
        mock_instance = MagicMock()
        mock_instance.get_supported_languages.return_value = ["en", "fr", "es", "de"]
        mock_instance.detect_language.return_value = [
            {"language": "en", "confidence": 0.9},
            {"language": "fr", "confidence": 0.05},
            {"language": "de", "confidence": 0.03},
        ]

        # Make the mock class return our mock instance
        mock_cls.return_value = mock_instance

        # Patch the global model instance
        with patch("src.models.translation.translation_model", mock_instance):
            yield mock_instance


def test_detect_language_endpoint(client, mock_model):
    """
    Test language detection endpoint.
    """
    response = client.post(
        "/detect_language",
        json={
            "text": "Hello, how are you?",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Check response
    assert "detections" in data
    assert "processing_time" in data

    # Check detections
    detections = data["detections"]
    assert len(detections) == 3  # The mock returns 3 detections
    assert detections[0]["language"] == "en"
    assert detections[0]["confidence"] == 0.9

    # Check that detect_language was called with correct parameters
    mock_model.detect_language.assert_called_with(
        text="Hello, how are you?",
        top_k=1,
    )


def test_detect_language_endpoint_top_k(client, mock_model):
    """
    Test language detection endpoint with top_k parameter.
    """
    response = client.post(
        "/detect_language",
        json={
            "text": "Hello, how are you?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Check detections
    detections = data["detections"]
    assert len(detections) == 3
    assert detections[0]["language"] == "en"
    assert detections[1]["language"] == "fr"
    assert detections[2]["language"] == "de"

    # Check that detect_language was called with correct parameters
    mock_model.detect_language.assert_called_with(
        text="Hello, how are you?",
        top_k=3,
    )


def test_detect_language_endpoint_error(client, mock_model):
    """
    Test language detection endpoint error handling.
    """
    # Make the mock model raise an exception
    mock_model.detect_language.side_effect = Exception("Language detection failed")

    response = client.post(
        "/detect_language",
        json={
            "text": "Hello, how are you?",
        },
    )

    assert response.status_code == 500
    data = response.json()

    # Check error response
    assert "detail" in data
    error_details = data["detail"]
    assert "detail" in error_details
    assert error_details["detail"] == "Language detection failed: Language detection failed"
    assert "error_type" in error_details
    assert error_details["error_type"] == "Exception"
    assert "request_id" in error_details


def test_detect_language_endpoint_validation(client):
    """
    Test language detection endpoint validation.
    """
    # Test with empty text
    response = client.post(
        "/detect_language",
        json={
            "text": "",
        },
    )

    # Empty text is valid, so we expect 200
    assert response.status_code == 200

    # Test with invalid top_k
    response = client.post(
        "/detect_language",
        json={
            "text": "Hello",
            "top_k": 0,  # Must be >= 1
        },
    )

    assert response.status_code == 422  # Validation error

    # Test with invalid top_k
    response = client.post(
        "/detect_language",
        json={
            "text": "Hello",
            "top_k": 11,  # Must be <= 10
        },
    )

    assert response.status_code == 422  # Validation error
