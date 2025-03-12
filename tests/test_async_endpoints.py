"""
Tests for the async translation endpoints.

This module contains tests for the async translation endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.utils.task_store import TaskStatus


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
        mock_instance.detect_language.return_value = [{"language": "en", "confidence": 0.9}]

        # Make the mock class return our mock instance
        mock_cls.return_value = mock_instance

        # Patch the global model instance
        with patch("src.models.translation.translation_model", mock_instance):
            yield mock_instance


@pytest.fixture
def mock_task_store():
    """
    Mock task store fixture.

    This creates a mock TaskStore that doesn't actually store tasks.
    """
    # Create a mock task
    mock_task = MagicMock()
    mock_task.task_id = "test-task-id"
    mock_task.status = TaskStatus.PENDING
    mock_task.created_at = "2023-01-01T00:00:00"
    mock_task.completed_at = None
    mock_task.result = None
    mock_task.error = None

    # Create a mock store
    mock_store = MagicMock()
    mock_store.create_task.return_value = mock_task
    mock_store.get_task.return_value = mock_task

    # Patch the task_store module
    with patch("src.api.endpoints.task_store", mock_store):
        yield mock_store, mock_task


def test_async_translate_endpoint(client, mock_model, mock_task_store):
    """
    Test async translation endpoint.
    """
    mock_store, mock_task = mock_task_store

    response = client.post(
        "/async/translate",
        json={
            "text": "Hello, how are you?",
            "options": {
                "source_lang": "en",
                "target_lang": "fr",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Check response
    assert data["task_id"] == mock_task.task_id
    assert data["status"] == TaskStatus.PENDING
    assert data["created_at"] == mock_task.created_at

    # Check that task was created
    mock_store.create_task.assert_called_once_with("translate", None)


def test_async_translate_endpoint_with_callback(client, mock_model, mock_task_store):
    """
    Test async translation endpoint with callback URL.
    """
    mock_store, mock_task = mock_task_store

    response = client.post(
        "/async/translate",
        json={
            "text": "Hello, how are you?",
            "options": {
                "source_lang": "en",
                "target_lang": "fr",
            },
            "callback_url": "https://example.com/callback",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Check response
    assert data["task_id"] == mock_task.task_id

    # Check that task was created with callback URL
    mock_store.create_task.assert_called_once_with("translate", "https://example.com/callback")


def test_async_batch_translate_endpoint(client, mock_model, mock_task_store):
    """
    Test async batch translation endpoint.
    """
    mock_store, mock_task = mock_task_store

    response = client.post(
        "/async/batch_translate",
        json={
            "texts": ["Hello", "World"],
            "options": {
                "source_lang": "en",
                "target_lang": "fr",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Check response
    assert data["task_id"] == mock_task.task_id
    assert data["status"] == TaskStatus.PENDING
    assert data["created_at"] == mock_task.created_at

    # Check that task was created
    mock_store.create_task.assert_called_once_with("batch_translate", None)


def test_async_status_endpoint(client, mock_task_store):
    """
    Test async status endpoint.
    """
    mock_store, mock_task = mock_task_store

    response = client.get(f"/async/status/{mock_task.task_id}")

    assert response.status_code == 200
    data = response.json()

    # Check response
    assert data["task_id"] == mock_task.task_id
    assert data["status"] == mock_task.status
    assert data["created_at"] == mock_task.created_at
    assert data["completed_at"] == mock_task.completed_at

    # Check that task was retrieved
    mock_store.get_task.assert_called_once_with(mock_task.task_id)


def test_async_status_endpoint_completed(client, mock_task_store):
    """
    Test async status endpoint with completed task.
    """
    mock_store, mock_task = mock_task_store

    # Set task as completed
    mock_task.status = TaskStatus.COMPLETED
    mock_task.completed_at = "2023-01-01T00:01:00"
    mock_task.result = {
        "translated_text": "Bonjour, comment ça va?",
        "source_lang": "en",
        "target_lang": "fr",
        "processing_time": 0.5,
    }

    response = client.get(f"/async/status/{mock_task.task_id}")

    assert response.status_code == 200
    data = response.json()

    # Check response
    assert data["task_id"] == mock_task.task_id
    assert data["status"] == TaskStatus.COMPLETED
    assert data["created_at"] == mock_task.created_at
    assert data["completed_at"] == mock_task.completed_at
    assert data["result"] == mock_task.result


def test_async_status_endpoint_failed(client, mock_task_store):
    """
    Test async status endpoint with failed task.
    """
    mock_store, mock_task = mock_task_store

    # Set task as failed
    mock_task.status = TaskStatus.FAILED
    mock_task.completed_at = "2023-01-01T00:01:00"
    mock_task.error = "Translation failed"

    response = client.get(f"/async/status/{mock_task.task_id}")

    assert response.status_code == 200
    data = response.json()

    # Check response
    assert data["task_id"] == mock_task.task_id
    assert data["status"] == TaskStatus.FAILED
    assert data["created_at"] == mock_task.created_at
    assert data["completed_at"] == mock_task.completed_at
    assert data["error"] == mock_task.error


def test_async_status_endpoint_not_found(client, mock_task_store):
    """
    Test async status endpoint with non-existent task.
    """
    mock_store, _ = mock_task_store

    # Make get_task return None
    mock_store.get_task.return_value = None

    response = client.get("/async/status/non-existent")

    assert response.status_code == 404
    data = response.json()

    # Check error response
    assert "detail" in data
    assert "Task not found" in data["detail"]["detail"]
