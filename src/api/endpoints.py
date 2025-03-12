"""
API endpoints for the Translation Service.

This module contains FastAPI route handlers for the Translation Service API.
"""

import time
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from src import __version__
from src.api.models import (
    AsyncBatchTranslationRequest,
    AsyncTranslationRequest,
    AsyncTranslationResponse,
    AsyncTranslationStatusResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    ConfigResponse,
    ErrorResponse,
    HealthResponse,
    LanguageDetectionRequest,
    LanguageDetectionResponse,
    TranslationOptions,
    TranslationRequest,
    TranslationResponse,
)
from src.config import settings
from src.logging_setup import logger
from src.models.translation import get_model
from src.utils.cache import translation_cache
from src.utils.metrics import (
    TASK_COUNT,
    TASK_LATENCY,
    TRANSLATION_COUNT,
    TRANSLATION_LATENCY,
    TRANSLATION_TEXT_LENGTH,
)
from src.utils.task_store import TaskStatus, task_store

# Create API router
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns basic information about the service status.
    """
    return {
        "status": "ok",
        "version": __version__,
    }


@router.get("/ready", response_model=HealthResponse, tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint.

    Checks if the service is ready to accept requests.
    """
    try:
        # Check if model is loaded
        model = get_model()

        return {
            "status": "ready",
            "version": __version__,
        }
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "version": __version__,
            },
        )


@router.get("/live", response_model=HealthResponse, tags=["Health"])
async def liveness_check():
    """
    Liveness check endpoint.

    Checks if the service is alive.
    """
    return {
        "status": "alive",
        "version": __version__,
    }


@router.get("/config", response_model=ConfigResponse, tags=["Configuration"])
async def get_config():
    """
    Get service configuration.

    Returns information about the current service configuration.
    """
    model = get_model()

    return {
        "model_size": settings.model.model_size,
        "device": settings.model.device,
        "compute_type": settings.model.compute_type,
        "supported_languages": model.get_supported_languages(),
    }


@router.post("/detect_language", response_model=LanguageDetectionResponse, tags=["Translation"])
async def detect_language(
    request: LanguageDetectionRequest,
    background_tasks: BackgroundTasks,
    req: Request,
):
    """
    Detect the language of the given text.

    Args:
        request: Language detection request
        background_tasks: Background tasks
        req: FastAPI request object

    Returns:
        Language detection response
    """
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())

    # Add request ID to logger context
    logger.bind(request_id=request_id)

    try:
        # Start timing
        start_time = time.time()

        # Get model
        model = get_model()

        # Detect language
        detections = model.detect_language(
            text=request.text,
            top_k=request.top_k,
        )

        # Calculate processing time
        processing_time = time.time() - start_time

        # Log successful language detection
        logger.info(
            "Language detection successful",
            request_id=request_id,
            text_length=len(request.text),
            processing_time=processing_time,
            detections=detections,
        )

        return {
            "detections": detections,
            "processing_time": processing_time,
        }

    except Exception as e:
        # Log error
        logger.error(
            "Language detection failed",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        # Return error response
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail=f"Language detection failed: {str(e)}",
                error_type=type(e).__name__,
                request_id=request_id,
            ).model_dump(),
        )


@router.post("/translate", response_model=TranslationResponse, tags=["Translation"])
async def translate_text(
    request: TranslationRequest,
    background_tasks: BackgroundTasks,
    req: Request,
):
    """
    Translate text from source language to target language.

    If source_lang is not provided, the language will be auto-detected.

    Args:
        request: Translation request
        background_tasks: Background tasks
        req: FastAPI request object

    Returns:
        Translation response
    """
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())

    # Add request ID to logger context
    logger.bind(request_id=request_id)

    try:
        # Start timing
        start_time = time.time()

        # Get model
        model = get_model()

        # Auto-detect source language if not provided
        source_lang = request.options.source_lang
        if source_lang is None:
            logger.info("Auto-detecting source language", request_id=request_id)
            detections = model.detect_language(text=request.text, top_k=1)
            if not detections:
                raise ValueError("Could not detect language")
            source_lang = detections[0]["language"]
            logger.info(
                "Detected source language",
                request_id=request_id,
                source_lang=source_lang,
            )

        # Perform translation
        translated_text = model.translate(
            text=request.text,
            source_lang=source_lang,
            target_lang=request.options.target_lang,
            beam_size=request.options.beam_size,
            max_length=request.options.max_length,
        )

        # Calculate processing time
        processing_time = time.time() - start_time

        # Record metrics
        TRANSLATION_COUNT.labels(
            source_lang=source_lang,
            target_lang=request.options.target_lang,
            status="success",
        ).inc()
        TRANSLATION_LATENCY.labels(
            source_lang=source_lang,
            target_lang=request.options.target_lang,
        ).observe(processing_time)
        TRANSLATION_TEXT_LENGTH.labels(
            source_lang=source_lang,
            target_lang=request.options.target_lang,
        ).observe(len(request.text))

        # Log successful translation
        logger.info(
            "Translation successful",
            request_id=request_id,
            source_lang=source_lang,
            target_lang=request.options.target_lang,
            text_length=len(request.text),
            processing_time=processing_time,
        )

        return {
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": request.options.target_lang,
            "processing_time": processing_time,
        }

    except Exception as e:
        # Record error metrics
        TRANSLATION_COUNT.labels(
            source_lang=request.options.source_lang or "unknown",
            target_lang=request.options.target_lang,
            status="error",
        ).inc()

        # Log error
        logger.error(
            "Translation failed",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        # Return error response
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail=f"Translation failed: {str(e)}",
                error_type=type(e).__name__,
                request_id=request_id,
            ).model_dump(),
        )


@router.post("/batch_translate", response_model=BatchTranslationResponse, tags=["Translation"])
async def batch_translate_text(
    request: BatchTranslationRequest,
    background_tasks: BackgroundTasks,
    req: Request,
):
    """
    Translate multiple texts from source language to target language.

    If source_lang is not provided, the language will be auto-detected for each text.

    Args:
        request: Batch translation request
        background_tasks: Background tasks
        req: FastAPI request object

    Returns:
        Batch translation response
    """
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())

    # Add request ID to logger context
    logger.bind(request_id=request_id)

    try:
        # Start timing
        start_time = time.time()

        # Get model
        model = get_model()

        # Perform translations
        translations = []
        source_lang = request.options.source_lang

        for text in request.texts:
            # Auto-detect source language if not provided
            current_source_lang = source_lang
            if current_source_lang is None:
                detections = model.detect_language(text=text, top_k=1)
                if not detections:
                    raise ValueError("Could not detect language")
                current_source_lang = detections[0]["language"]
                logger.debug(
                    "Detected source language",
                    text=text[:50],
                    source_lang=current_source_lang,
                )

            translated_text = model.translate(
                text=text,
                source_lang=current_source_lang,
                target_lang=request.options.target_lang,
                beam_size=request.options.beam_size,
                max_length=request.options.max_length,
            )
            translations.append(translated_text)

            # Record individual translation metrics
            TRANSLATION_COUNT.labels(
                source_lang=current_source_lang,
                target_lang=request.options.target_lang,
                status="success",
            ).inc()
            TRANSLATION_TEXT_LENGTH.labels(
                source_lang=current_source_lang,
                target_lang=request.options.target_lang,
            ).observe(len(text))

        # Calculate processing time
        processing_time = time.time() - start_time

        # Record batch metrics
        TRANSLATION_LATENCY.labels(
            source_lang=source_lang or "auto-detected",
            target_lang=request.options.target_lang,
        ).observe(
            processing_time / len(request.texts)
        )  # Average time per translation

        # Log successful batch translation
        logger.info(
            "Batch translation successful",
            request_id=request_id,
            source_lang=source_lang or "auto-detected",
            target_lang=request.options.target_lang,
            batch_size=len(request.texts),
            processing_time=processing_time,
        )

        return {
            "translations": translations,
            "source_lang": source_lang or "auto-detected",
            "target_lang": request.options.target_lang,
            "processing_time": processing_time,
        }

    except Exception as e:
        # Record error metrics
        TRANSLATION_COUNT.labels(
            source_lang=request.options.source_lang or "unknown",
            target_lang=request.options.target_lang,
            status="error",
        ).inc()

        # Log error
        logger.error(
            "Batch translation failed",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        # Return error response
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail=f"Batch translation failed: {str(e)}",
                error_type=type(e).__name__,
                request_id=request_id,
            ).model_dump(),
        )


@router.post(
    "/async/translate",
    response_model=AsyncTranslationResponse,
    tags=["Async Translation"],
)
async def async_translate_text(
    request: AsyncTranslationRequest,
    background_tasks: BackgroundTasks,
    req: Request,
):
    """
    Submit an asynchronous translation request.

    Args:
        request: Async translation request
        background_tasks: Background tasks
        req: FastAPI request object

    Returns:
        Async translation response with task ID
    """
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())

    # Add request ID to logger context
    logger.bind(request_id=request_id)

    try:
        # Create a new task
        task = task_store.create_task("translate", request.callback_url)

        # Record task metrics
        TASK_COUNT.labels(task_type="translate", status="pending").inc()

        # Add task to background tasks
        background_tasks.add_task(
            process_async_translation,
            task_id=task.task_id,
            text=request.text,
            options=request.options,
        )

        logger.info(
            "Async translation task created",
            request_id=request_id,
            task_id=task.task_id,
            text_length=len(request.text),
        )

        return {
            "task_id": task.task_id,
            "status": task.status,
            "created_at": task.created_at,
        }

    except Exception as e:
        # Record error metrics
        TASK_COUNT.labels(task_type="translate", status="error").inc()

        # Log error
        logger.error(
            "Failed to create async translation task",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        # Return error response
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail=f"Failed to create async translation task: {str(e)}",
                error_type=type(e).__name__,
                request_id=request_id,
            ).model_dump(),
        )


@router.post(
    "/async/batch_translate",
    response_model=AsyncTranslationResponse,
    tags=["Async Translation"],
)
async def async_batch_translate_text(
    request: AsyncBatchTranslationRequest,
    background_tasks: BackgroundTasks,
    req: Request,
):
    """
    Submit an asynchronous batch translation request.

    Args:
        request: Async batch translation request
        background_tasks: Background tasks
        req: FastAPI request object

    Returns:
        Async translation response with task ID
    """
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())

    # Add request ID to logger context
    logger.bind(request_id=request_id)

    try:
        # Create a new task
        task = task_store.create_task("batch_translate", request.callback_url)

        # Record task metrics
        TASK_COUNT.labels(task_type="batch_translate", status="pending").inc()

        # Add task to background tasks
        background_tasks.add_task(
            process_async_batch_translation,
            task_id=task.task_id,
            texts=request.texts,
            options=request.options,
        )

        logger.info(
            "Async batch translation task created",
            request_id=request_id,
            task_id=task.task_id,
            batch_size=len(request.texts),
        )

        return {
            "task_id": task.task_id,
            "status": task.status,
            "created_at": task.created_at,
        }

    except Exception as e:
        # Record error metrics
        TASK_COUNT.labels(task_type="batch_translate", status="error").inc()

        # Log error
        logger.error(
            "Failed to create async batch translation task",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        # Return error response
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail=f"Failed to create async batch translation task: {str(e)}",
                error_type=type(e).__name__,
                request_id=request_id,
            ).model_dump(),
        )


@router.get(
    "/async/status/{task_id}",
    response_model=AsyncTranslationStatusResponse,
    tags=["Async Translation"],
)
async def get_async_translation_status(task_id: str):
    """
    Get the status of an asynchronous translation task.

    Args:
        task_id: Task ID

    Returns:
        Async translation status response
    """
    # Get task
    task = task_store.get_task(task_id)

    # Check if task exists
    if not task:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                detail=f"Task not found: {task_id}",
                error_type="TaskNotFound",
            ).model_dump(),
        )

    # Return task status
    response = {
        "task_id": task.task_id,
        "status": task.status,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
    }

    # Add result or error if available
    if task.status == TaskStatus.COMPLETED:
        response["result"] = task.result
    elif task.status == TaskStatus.FAILED:
        response["error"] = task.error

    return response


async def process_async_translation(task_id: str, text: str, options: TranslationOptions):
    """
    Process an asynchronous translation task.

    Args:
        task_id: Task ID
        text: Text to translate
        options: Translation options
    """
    # Get task
    task = task_store.get_task(task_id)
    if not task:
        logger.error("Task not found", task_id=task_id)
        return

    # Mark task as processing
    task.start()
    TASK_COUNT.labels(task_type="translate", status="processing").inc()

    start_time = time.time()

    try:
        # Start timing
        start_time = time.time()

        # Get model
        model = get_model()

        # Auto-detect source language if not provided
        source_lang = options.source_lang
        if source_lang is None:
            logger.info("Auto-detecting source language", task_id=task_id)
            detections = model.detect_language(text=text, top_k=1)
            if not detections:
                raise ValueError("Could not detect language")
            source_lang = detections[0]["language"]
            logger.info("Detected source language", task_id=task_id, source_lang=source_lang)

        # Perform translation
        translated_text = model.translate(
            text=text,
            source_lang=source_lang,
            target_lang=options.target_lang,
            beam_size=options.beam_size,
            max_length=options.max_length,
        )

        # Calculate processing time
        processing_time = time.time() - start_time

        # Record metrics
        TRANSLATION_COUNT.labels(
            source_lang=source_lang,
            target_lang=options.target_lang,
            status="success",
        ).inc()
        TRANSLATION_LATENCY.labels(
            source_lang=source_lang,
            target_lang=options.target_lang,
        ).observe(processing_time)
        TRANSLATION_TEXT_LENGTH.labels(
            source_lang=source_lang,
            target_lang=options.target_lang,
        ).observe(len(text))

        # Create result
        result = {
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": options.target_lang,
            "processing_time": processing_time,
        }

        # Mark task as completed
        task.complete(result)
        TASK_COUNT.labels(task_type="translate", status="completed").inc()
        TASK_LATENCY.labels(task_type="translate").observe(time.time() - start_time)

        # Log successful translation
        logger.info(
            "Async translation completed",
            task_id=task_id,
            source_lang=source_lang,
            target_lang=options.target_lang,
            text_length=len(text),
            processing_time=processing_time,
        )

    except Exception as e:
        # Record error metrics
        TRANSLATION_COUNT.labels(
            source_lang=options.source_lang or "unknown",
            target_lang=options.target_lang,
            status="error",
        ).inc()
        TASK_COUNT.labels(task_type="translate", status="failed").inc()
        TASK_LATENCY.labels(task_type="translate").observe(time.time() - start_time)

        # Log error
        logger.error(
            "Async translation failed",
            task_id=task_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        # Mark task as failed
        task.fail(str(e))


async def process_async_batch_translation(
    task_id: str, texts: List[str], options: TranslationOptions
):
    """
    Process an asynchronous batch translation task.

    Args:
        task_id: Task ID
        texts: Texts to translate
        options: Translation options
    """
    # Get task
    task = task_store.get_task(task_id)
    if not task:
        logger.error("Task not found", task_id=task_id)
        return

    # Mark task as processing
    task.start()
    TASK_COUNT.labels(task_type="batch_translate", status="processing").inc()

    start_time = time.time()

    try:
        # Start timing
        start_time = time.time()

        # Get model
        model = get_model()

        # Perform translations
        translations = []
        source_lang = options.source_lang

        for text in texts:
            # Auto-detect source language if not provided
            current_source_lang = source_lang
            if current_source_lang is None:
                detections = model.detect_language(text=text, top_k=1)
                if not detections:
                    raise ValueError("Could not detect language")
                current_source_lang = detections[0]["language"]
                logger.debug(
                    "Detected source language",
                    text=text[:50],
                    source_lang=current_source_lang,
                )

            translated_text = model.translate(
                text=text,
                source_lang=current_source_lang,
                target_lang=options.target_lang,
                beam_size=options.beam_size,
                max_length=options.max_length,
            )
            translations.append(translated_text)

            # Record individual translation metrics
            TRANSLATION_COUNT.labels(
                source_lang=current_source_lang,
                target_lang=options.target_lang,
                status="success",
            ).inc()
            TRANSLATION_TEXT_LENGTH.labels(
                source_lang=current_source_lang,
                target_lang=options.target_lang,
            ).observe(len(text))

        # Calculate processing time
        processing_time = time.time() - start_time

        # Record batch metrics
        TRANSLATION_LATENCY.labels(
            source_lang=source_lang or "auto-detected",
            target_lang=options.target_lang,
        ).observe(
            processing_time / len(texts)
        )  # Average time per translation

        # Create result
        result = {
            "translations": translations,
            "source_lang": source_lang or "auto-detected",
            "target_lang": options.target_lang,
            "processing_time": processing_time,
        }

        # Mark task as completed
        task.complete(result)
        TASK_COUNT.labels(task_type="batch_translate", status="completed").inc()
        TASK_LATENCY.labels(task_type="batch_translate").observe(time.time() - start_time)

        # Log successful batch translation
        logger.info(
            "Async batch translation completed",
            task_id=task_id,
            source_lang=source_lang or "auto-detected",
            target_lang=options.target_lang,
            batch_size=len(texts),
            processing_time=processing_time,
        )

    except Exception as e:
        # Record error metrics
        TRANSLATION_COUNT.labels(
            source_lang=options.source_lang or "unknown",
            target_lang=options.target_lang,
            status="error",
        ).inc()

        # Log error
        logger.error(
            "Async batch translation failed",
            task_id=task_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        # Mark task as failed
        task.fail(str(e))


@router.get("/cache/stats", tags=["Cache"])
async def get_cache_stats():
    """
    Get cache statistics.

    Returns information about the translation cache.
    """
    return translation_cache.get_stats()


@router.post("/cache/clear", tags=["Cache"])
async def clear_cache():
    """
    Clear the translation cache.

    Removes all cached translations.
    """
    translation_cache.clear()
    return {"status": "ok", "message": "Cache cleared"}
