"""
Task store for async translation tasks.

This module provides a simple in-memory store for tracking async translation tasks.
"""

import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx

from src.logging_setup import logger


class TaskStatus(str, Enum):
    """Task status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    """Task class for async operations."""

    def __init__(self, task_type: str, callback_url: Optional[str] = None):
        """
        Initialize a new task.

        Args:
            task_type: Type of task (e.g., "translate", "batch_translate")
            callback_url: URL to call when the task is complete
        """
        self.task_id = str(uuid.uuid4())
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.callback_url = callback_url

    def start(self):
        """Mark the task as processing."""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.now().isoformat()

    def complete(self, result: Any):
        """
        Mark the task as completed.

        Args:
            result: Task result
        """
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        self.result = result

        # Call callback URL if provided
        if self.callback_url:
            self._send_callback()

    def fail(self, error: str):
        """
        Mark the task as failed.

        Args:
            error: Error message
        """
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        self.error = error

        # Call callback URL if provided
        if self.callback_url:
            self._send_callback()

    def _send_callback(self):
        """Send callback to the provided URL."""
        try:
            # Create payload
            payload = {
                "task_id": self.task_id,
                "status": self.status,
                "created_at": self.created_at,
                "completed_at": self.completed_at,
            }

            # Add result or error
            if self.status == TaskStatus.COMPLETED:
                payload["result"] = self.result
            elif self.status == TaskStatus.FAILED:
                payload["error"] = self.error

            # Send callback
            httpx.post(self.callback_url, json=payload, timeout=10)
            logger.info("Callback sent", task_id=self.task_id, url=self.callback_url)

        except Exception as e:
            logger.error(
                "Failed to send callback",
                task_id=self.task_id,
                url=self.callback_url,
                error=str(e),
            )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert task to dictionary.

        Returns:
            Task as dictionary
        """
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "callback_url": self.callback_url,
        }


class TaskStore:
    """Simple in-memory task store."""

    def __init__(self):
        """Initialize the task store."""
        self.tasks: Dict[str, Task] = {}

    def create_task(self, task_type: str, callback_url: Optional[str] = None) -> Task:
        """
        Create a new task.

        Args:
            task_type: Type of task
            callback_url: URL to call when the task is complete

        Returns:
            New task
        """
        task = Task(task_type, callback_url)
        self.tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task or None if not found
        """
        return self.tasks.get(task_id)

    def list_tasks(self, limit: int = 100, offset: int = 0) -> List[Task]:
        """
        List tasks.

        Args:
            limit: Maximum number of tasks to return
            offset: Offset for pagination

        Returns:
            List of tasks
        """
        return list(self.tasks.values())[offset : offset + limit]

    def cleanup_old_tasks(self, max_age_seconds: int = 86400):
        """
        Remove old tasks from the store.

        Args:
            max_age_seconds: Maximum age of tasks to keep (in seconds)
        """
        now = time.time()
        to_remove = []

        for task_id, task in self.tasks.items():
            created_time = datetime.fromisoformat(task.created_at).timestamp()
            if now - created_time > max_age_seconds:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.tasks[task_id]

        logger.info("Cleaned up old tasks", removed_count=len(to_remove))


# Create global task store instance
task_store = TaskStore()
