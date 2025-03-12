"""
API models for the Translation Service.

This module contains Pydantic models for request and response validation.
"""

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class TranslationOptions(BaseModel):
    """Options for translation."""

    source_lang: Optional[str] = Field(
        default=None, description="Source language code (auto-detect if not provided)"
    )
    target_lang: str = Field(default="fr", description="Target language code")
    beam_size: int = Field(default=5, ge=1, le=10, description="Beam size for beam search")
    max_length: int = Field(default=200, ge=1, description="Maximum output length")
    preserve_formatting: bool = Field(
        default=False, description="Preserve formatting in translation"
    )

    @field_validator("source_lang", "target_lang")
    @classmethod
    def validate_language(cls, v: str) -> str:
        # Basic validation for language codes
        if v is not None and (len(v) < 2 or len(v) > 5):
            raise ValueError(f"Invalid language code: {v}")
        return v


class TranslationRequest(BaseModel):
    """Request model for translation endpoint."""

    text: str = Field(..., description="Text to translate")
    options: TranslationOptions = Field(
        default_factory=TranslationOptions, description="Translation options"
    )


class TranslationResponse(BaseModel):
    """Response model for translation endpoint."""

    translated_text: str = Field(..., description="Translated text")
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")
    processing_time: float = Field(..., description="Processing time in seconds")


class BatchTranslationRequest(BaseModel):
    """Request model for batch translation endpoint."""

    texts: List[str] = Field(..., description="List of texts to translate")
    options: TranslationOptions = Field(
        default_factory=TranslationOptions, description="Translation options"
    )


class BatchTranslationResponse(BaseModel):
    """Response model for batch translation endpoint."""

    translations: List[str] = Field(..., description="List of translated texts")
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")
    processing_time: float = Field(..., description="Processing time in seconds")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")


class ConfigResponse(BaseModel):
    """Response model for configuration endpoint."""

    model_size: str = Field(..., description="Model size")
    device: str = Field(..., description="Device")
    compute_type: str = Field(..., description="Compute type")
    supported_languages: List[str] = Field(..., description="List of supported language codes")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    detail: str = Field(..., description="Error detail")
    error_type: Optional[str] = Field(None, description="Error type")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class LanguageDetectionRequest(BaseModel):
    """Request model for language detection endpoint."""

    text: str = Field(..., description="Text to detect language for")
    top_k: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Number of top language predictions to return",
    )


class LanguageDetectionResponse(BaseModel):
    """Response model for language detection endpoint."""

    detections: List[Dict[str, Union[str, float]]] = Field(
        ..., description="List of detected languages with confidence scores"
    )
    processing_time: float = Field(..., description="Processing time in seconds")


class AsyncTranslationRequest(BaseModel):
    """Request model for async translation endpoint."""

    text: str = Field(..., description="Text to translate")
    options: TranslationOptions = Field(
        default_factory=TranslationOptions, description="Translation options"
    )
    callback_url: Optional[str] = Field(
        None, description="URL to call when translation is complete"
    )


class AsyncBatchTranslationRequest(BaseModel):
    """Request model for async batch translation endpoint."""

    texts: List[str] = Field(..., description="List of texts to translate")
    options: TranslationOptions = Field(
        default_factory=TranslationOptions, description="Translation options"
    )
    callback_url: Optional[str] = Field(
        None, description="URL to call when translation is complete"
    )


class AsyncTranslationResponse(BaseModel):
    """Response model for async translation endpoint."""

    task_id: str = Field(..., description="Task ID for tracking the translation")
    status: str = Field(..., description="Task status (pending, processing, completed, failed)")
    created_at: str = Field(..., description="Timestamp when the task was created")


class AsyncTranslationStatusResponse(BaseModel):
    """Response model for async translation status endpoint."""

    task_id: str = Field(..., description="Task ID for tracking the translation")
    status: str = Field(..., description="Task status (pending, processing, completed, failed)")
    created_at: str = Field(..., description="Timestamp when the task was created")
    completed_at: Optional[str] = Field(None, description="Timestamp when the task was completed")
    result: Optional[Union[TranslationResponse, BatchTranslationResponse]] = Field(
        None, description="Translation result"
    )
    error: Optional[str] = Field(None, description="Error message if the task failed")
