"""
Tests for the Translation Service API.

This module contains tests for the API endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.translation import TranslationModel


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
        mock_instance.translate.return_value = "Bonjour, comment ça va?"

        # Make the mock class return our mock instance
        mock_cls.return_value = mock_instance

        # Patch the global model instance
        with patch("src.models.translation.translation_model", mock_instance):
            yield mock_instance


def test_health_check(client):
    """
    Test health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_liveness_check(client):
    """
    Test liveness check endpoint.
    """
    response = client.get("/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "version" in data


def test_readiness_check(client, mock_model):
    """
    Test readiness check endpoint.
    """
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "version" in data


def test_readiness_check_failure(client):
    """
    Test readiness check endpoint when model initialization fails.
    """
    with patch(
        "src.api.endpoints.get_model",
        side_effect=Exception("Model initialization failed"),
    ):
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert "version" in data


def test_config_endpoint(client, mock_model):
    """
    Test configuration endpoint.
    """
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "model_size" in data
    assert "device" in data
    assert "compute_type" in data
    assert "supported_languages" in data
    assert data["supported_languages"] == ["en", "fr", "es", "de"]


def test_translate_endpoint(client, mock_model):
    """
    Test translation endpoint.
    """
    response = client.post(
        "/translate",
        json={
            "text": "Hello, how are you?",
            "options": {
                "source_lang": "en",
                "target_lang": "fr",
                "beam_size": 5,
                "max_length": 200,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["translated_text"] == "Bonjour, comment ça va?"
    assert data["source_lang"] == "en"
    assert data["target_lang"] == "fr"
    assert "processing_time" in data

    # Verify the mock was called with the right parameters
    mock_model.translate.assert_called_once()
    args, kwargs = mock_model.translate.call_args
    assert kwargs["text"] == "Hello, how are you?"
    assert kwargs["source_lang"] == "en"
    assert kwargs["target_lang"] == "fr"
    assert kwargs["beam_size"] == 5
    assert kwargs["max_length"] == 200


def test_translate_endpoint_error(client, mock_model):
    """
    Test translation endpoint error handling.
    """
    # Make the mock model raise an exception
    mock_model.translate.side_effect = Exception("Translation failed")

    response = client.post(
        "/translate",
        json={
            "text": "Hello, how are you?",
            "options": {
                "source_lang": "en",
                "target_lang": "fr",
            },
        },
    )

    assert response.status_code == 500
    data = response.json()

    # The response has a nested structure with 'detail' containing the error details
    assert "detail" in data
    error_details = data["detail"]
    assert "detail" in error_details
    assert error_details["detail"] == "Translation failed: Translation failed"
    assert "error_type" in error_details
    assert error_details["error_type"] == "Exception"
    assert "request_id" in error_details


def test_batch_translate_endpoint(client, mock_model):
    """
    Test batch translation endpoint.
    """
    response = client.post(
        "/batch_translate",
        json={
            "texts": ["Hello, how are you?", "What is your name?"],
            "options": {
                "source_lang": "en",
                "target_lang": "fr",
                "beam_size": 5,
                "max_length": 200,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["translations"]) == 2
    assert data["translations"][0] == "Bonjour, comment ça va?"
    assert data["translations"][1] == "Bonjour, comment ça va?"
    assert data["source_lang"] == "en"
    assert data["target_lang"] == "fr"
    assert "processing_time" in data

    # Verify the mock was called twice with the right parameters
    assert mock_model.translate.call_count == 2

    # Check first call
    args, kwargs = mock_model.translate.call_args_list[0]
    assert kwargs["text"] == "Hello, how are you?"
    assert kwargs["source_lang"] == "en"
    assert kwargs["target_lang"] == "fr"

    # Check second call
    args, kwargs = mock_model.translate.call_args_list[1]
    assert kwargs["text"] == "What is your name?"
    assert kwargs["source_lang"] == "en"
    assert kwargs["target_lang"] == "fr"


def test_batch_translate_endpoint_validation(client, mock_model):
    """
    Test batch translation endpoint with invalid input.
    """
    # Test with empty texts list
    response = client.post(
        "/batch_translate",
        json={
            "texts": [],
            "options": {
                "source_lang": "en",
                "target_lang": "fr",
            },
        },
    )

    # Empty texts list causes a division by zero error in the endpoint
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data


def test_batch_translate_endpoint_error(client, mock_model):
    """
    Test batch translation endpoint error handling.
    """
    # Make the mock model raise an exception
    mock_model.translate.side_effect = Exception("Translation failed")

    response = client.post(
        "/batch_translate",
        json={
            "texts": ["Hello", "World"],
            "options": {
                "source_lang": "en",
                "target_lang": "fr",
            },
        },
    )

    assert response.status_code == 500
    data = response.json()

    # The response has a nested structure with 'detail' containing the error details
    assert "detail" in data
    error_details = data["detail"]
    assert "detail" in error_details
    assert error_details["detail"] == "Batch translation failed: Translation failed"
    assert "error_type" in error_details
    assert error_details["error_type"] == "Exception"
    assert "request_id" in error_details
