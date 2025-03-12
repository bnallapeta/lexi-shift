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
    BatchTranslationRequest,
    BatchTranslationResponse,
    ConfigResponse,
    ErrorResponse,
    HealthResponse,
    TranslationRequest,
    TranslationResponse,
)
from src.config import settings
from src.logging_setup import logger
from src.models.translation import get_model

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


@router.post("/translate", response_model=TranslationResponse, tags=["Translation"])
async def translate_text(
    request: TranslationRequest,
    background_tasks: BackgroundTasks,
    req: Request,
):
    """
    Translate text from source language to target language.
    
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
        
        # Perform translation
        translated_text = model.translate(
            text=request.text,
            source_lang=request.options.source_lang,
            target_lang=request.options.target_lang,
            beam_size=request.options.beam_size,
            max_length=request.options.max_length,
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log successful translation
        logger.info(
            "Translation successful",
            request_id=request_id,
            source_lang=request.options.source_lang,
            target_lang=request.options.target_lang,
            text_length=len(request.text),
            processing_time=processing_time,
        )
        
        return {
            "translated_text": translated_text,
            "source_lang": request.options.source_lang,
            "target_lang": request.options.target_lang,
            "processing_time": processing_time,
        }
    
    except Exception as e:
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
        for text in request.texts:
            translated_text = model.translate(
                text=text,
                source_lang=request.options.source_lang,
                target_lang=request.options.target_lang,
                beam_size=request.options.beam_size,
                max_length=request.options.max_length,
            )
            translations.append(translated_text)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log successful batch translation
        logger.info(
            "Batch translation successful",
            request_id=request_id,
            source_lang=request.options.source_lang,
            target_lang=request.options.target_lang,
            batch_size=len(request.texts),
            processing_time=processing_time,
        )
        
        return {
            "translations": translations,
            "source_lang": request.options.source_lang,
            "target_lang": request.options.target_lang,
            "processing_time": processing_time,
        }
    
    except Exception as e:
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