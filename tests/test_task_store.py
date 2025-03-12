"""
Tests for the task store.

This module contains tests for the task store implementation.
"""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.utils.task_store import Task, TaskStatus, TaskStore


@pytest.fixture
def task():
    """Create a task for testing."""
    return Task("translate")


@pytest.fixture
def task_store():
    """Create a task store for testing."""
    return TaskStore()


def test_task_init(task):
    """Test task initialization."""
    assert task.task_id is not None
    assert task.task_type == "translate"
    assert task.status == TaskStatus.PENDING
    assert task.created_at is not None
    assert task.started_at is None
    assert task.completed_at is None
    assert task.result is None
    assert task.error is None
    assert task.callback_url is None


def test_task_start(task):
    """Test task start method."""
    task.start()
    assert task.status == TaskStatus.PROCESSING
    assert task.started_at is not None


def test_task_complete(task):
    """Test task complete method."""
    result = {"translated_text": "Bonjour"}
    task.complete(result)
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None
    assert task.result == result
    assert task.error is None


def test_task_fail(task):
    """Test task fail method."""
    error = "Translation failed"
    task.fail(error)
    assert task.status == TaskStatus.FAILED
    assert task.completed_at is not None
    assert task.result is None
    assert task.error == error


def test_task_callback():
    """Test task callback."""
    with patch("httpx.post") as mock_post:
        # Create a task with a callback URL
        task = Task("translate", callback_url="https://example.com/callback")

        # Complete the task
        result = {"translated_text": "Bonjour"}
        task.complete(result)

        # Check that the callback was called
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://example.com/callback"
        assert "json" in kwargs
        assert kwargs["json"]["task_id"] == task.task_id
        assert kwargs["json"]["status"] == TaskStatus.COMPLETED
        assert kwargs["json"]["result"] == result


def test_task_callback_error():
    """Test task callback with error."""
    with (
        patch("httpx.post", side_effect=Exception("Connection error")),
        patch("src.utils.task_store.logger") as mock_logger,
    ):

        # Create a task with a callback URL
        task = Task("translate", callback_url="https://example.com/callback")

        # Complete the task
        task.complete({"translated_text": "Bonjour"})

        # Check that the error was logged
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert args[0] == "Failed to send callback"
        assert kwargs["task_id"] == task.task_id
        assert kwargs["url"] == "https://example.com/callback"
        assert "error" in kwargs


def test_task_to_dict(task):
    """Test task to_dict method."""
    task_dict = task.to_dict()
    assert task_dict["task_id"] == task.task_id
    assert task_dict["task_type"] == task.task_type
    assert task_dict["status"] == task.status
    assert task_dict["created_at"] == task.created_at
    assert task_dict["started_at"] == task.started_at
    assert task_dict["completed_at"] == task.completed_at
    assert task_dict["result"] == task.result
    assert task_dict["error"] == task.error
    assert task_dict["callback_url"] == task.callback_url


def test_task_store_create_task(task_store):
    """Test task store create_task method."""
    task = task_store.create_task("translate")
    assert task.task_id in task_store.tasks
    assert task_store.tasks[task.task_id] == task


def test_task_store_get_task(task_store):
    """Test task store get_task method."""
    task = task_store.create_task("translate")
    retrieved_task = task_store.get_task(task.task_id)
    assert retrieved_task == task

    # Test with non-existent task ID
    assert task_store.get_task("non-existent") is None


def test_task_store_list_tasks(task_store):
    """Test task store list_tasks method."""
    # Create some tasks
    tasks = [task_store.create_task("translate") for _ in range(5)]

    # List all tasks
    listed_tasks = task_store.list_tasks()
    assert len(listed_tasks) == 5

    # List with limit
    listed_tasks = task_store.list_tasks(limit=3)
    assert len(listed_tasks) == 3

    # List with offset
    listed_tasks = task_store.list_tasks(offset=2)
    assert len(listed_tasks) == 3

    # List with limit and offset
    listed_tasks = task_store.list_tasks(limit=2, offset=2)
    assert len(listed_tasks) == 2


def test_task_store_cleanup_old_tasks(task_store):
    """Test task store cleanup_old_tasks method."""
    # Create a task with an old timestamp
    task = task_store.create_task("translate")

    # Mock the created_at timestamp to be old
    old_time = (datetime.now() - timedelta(days=2)).isoformat()
    task.created_at = old_time

    # Create a recent task
    recent_task = task_store.create_task("translate")

    # Clean up old tasks
    task_store.cleanup_old_tasks(max_age_seconds=86400)  # 1 day

    # Check that the old task was removed
    assert task.task_id not in task_store.tasks

    # Check that the recent task is still there
    assert recent_task.task_id in task_store.tasks
