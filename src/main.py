"""
Main module for the Translation Service.

This module contains the FastAPI application and server configuration.
"""

import asyncio
import os
import platform
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Union

import psutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import start_http_server

from src import __version__
from src.api.endpoints import router as api_router
from src.config import settings
from src.logging_setup import logger, setup_logging
from src.models.translation import get_model
from src.utils.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    SYSTEM_CPU_USAGE,
    SYSTEM_MEMORY_USAGE,
    TASK_QUEUE_SIZE,
)
from src.utils.task_store import TaskStatus, task_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.

    This handles startup and shutdown events for the application.
    """
    # Set up logging
    setup_logging()

    # Log startup
    logger.info("Starting Translation Service", version=__version__)

    # Start Prometheus metrics server
    start_http_server(8001)
    logger.info("Started Prometheus metrics server on port 8001")

    # Initialize translation model
    try:
        logger.info("Initializing translation model")
        get_model()
        logger.info("Translation model initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize translation model", error=str(e), exc_info=True)

    # Start task cleanup task
    cleanup_task = asyncio.create_task(periodic_task_cleanup())

    # Start system metrics collection task
    metrics_task = asyncio.create_task(collect_system_metrics())

    # Yield control to the application
    yield

    # Log shutdown
    logger.info("Shutting down Translation Service")

    # Cancel background tasks
    for task in [cleanup_task, metrics_task]:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def periodic_task_cleanup():
    """Periodically clean up old tasks."""
    while True:
        try:
            # Clean up tasks older than 24 hours
            task_store.cleanup_old_tasks(max_age_seconds=86400)
            # Sleep for 1 hour
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            break
        except Exception as e:
            logger.error("Error in task cleanup", error=str(e), exc_info=True)
            # Sleep for 5 minutes before retrying
            await asyncio.sleep(300)


async def collect_system_metrics():
    """Collect system metrics periodically."""
    while True:
        try:
            # Collect memory metrics
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.labels(type="total").set(memory.total)
            SYSTEM_MEMORY_USAGE.labels(type="used").set(memory.used)
            SYSTEM_MEMORY_USAGE.labels(type="free").set(memory.available)

            # Collect CPU metrics
            cpu = psutil.cpu_times_percent(interval=1)
            SYSTEM_CPU_USAGE.labels(type="user").set(cpu.user)
            SYSTEM_CPU_USAGE.labels(type="system").set(cpu.system)
            SYSTEM_CPU_USAGE.labels(type="idle").set(cpu.idle)

            # Collect task queue metrics
            tasks = task_store.tasks
            pending_count = sum(1 for t in tasks.values() if t.status == TaskStatus.PENDING)
            processing_count = sum(1 for t in tasks.values() if t.status == TaskStatus.PROCESSING)
            completed_count = sum(1 for t in tasks.values() if t.status == TaskStatus.COMPLETED)
            failed_count = sum(1 for t in tasks.values() if t.status == TaskStatus.FAILED)

            TASK_QUEUE_SIZE.labels(status="pending").set(pending_count)
            TASK_QUEUE_SIZE.labels(status="processing").set(processing_count)
            TASK_QUEUE_SIZE.labels(status="completed").set(completed_count)
            TASK_QUEUE_SIZE.labels(status="failed").set(failed_count)

            # Sleep for 15 seconds
            await asyncio.sleep(15)

        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            break
        except Exception as e:
            logger.error("Error collecting system metrics", error=str(e), exc_info=True)
            # Sleep for 30 seconds before retrying
            await asyncio.sleep(30)


# Create FastAPI application
app = FastAPI(
    title="Translation Service",
    description="A high-performance text translation service using NLLB-200 models",
    version=__version__,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """
    Middleware to add a request ID to each request.

    This also tracks request metrics using Prometheus.

    Args:
        request: FastAPI request object
        call_next: Next middleware or route handler

    Returns:
        Response from the next middleware or route handler
    """
    # Generate request ID
    request_id = str(uuid.uuid4())

    # Add request ID to request state
    request.state.request_id = request_id

    # Get endpoint path for metrics
    endpoint = request.url.path

    # Start timing
    start_time = time.time()

    try:
        # Process request
        response = await call_next(request)

        # Record metrics
        REQUEST_COUNT.labels(endpoint=endpoint, status=response.status_code).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start_time)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        # Record error metrics
        REQUEST_COUNT.labels(endpoint=endpoint, status=500).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start_time)

        # Re-raise exception
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for the application.

    Args:
        request: FastAPI request object
        exc: Exception that was raised

    Returns:
        JSON response with error details
    """
    # Get request ID
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Log error
    logger.error(
        "Unhandled exception",
        request_id=request_id,
        url=str(request.url),
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
        exc_info=True,
    )

    # Return error response
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "error_type": type(exc).__name__,
            "request_id": request_id,
        },
    )


# Include API router
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.server.host,
        port=settings.server.port,
        log_level=settings.server.log_level,
        reload=settings.debug,
    )
