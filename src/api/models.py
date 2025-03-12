"""
API models for the Translation Service.

This module contains Pydantic models for request and response validation.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TranslationOptions(BaseModel):
    """Options for translation."""
    source_lang: str = Field(default="en", description="Source language code")
    target_lang: str = Field(default="fr", description="Target language code")
    beam_size: int = Field(default=5, ge=1, le=10, description="Beam size for beam search")
    max_length: int = Field(default=200, ge=1, description="Maximum output length")
    preserve_formatting: bool = Field(default=False, description="Preserve formatting in translation")
    
    @field_validator("source_lang", "target_lang")
    @classmethod
    def validate_language(cls, v: str) -> str:
        # Basic validation for language codes
        if len(v) < 2 or len(v) > 5:
            raise ValueError(f"Invalid language code: {v}")
        return v


class TranslationRequest(BaseModel):
    """Request model for translation endpoint."""
    text: str = Field(..., description="Text to translate")
    options: TranslationOptions = Field(default_factory=TranslationOptions, description="Translation options")


class TranslationResponse(BaseModel):
    """Response model for translation endpoint."""
    translated_text: str = Field(..., description="Translated text")
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")
    processing_time: float = Field(..., description="Processing time in seconds")


class BatchTranslationRequest(BaseModel):
    """Request model for batch translation endpoint."""
    texts: List[str] = Field(..., description="List of texts to translate")
    options: TranslationOptions = Field(default_factory=TranslationOptions, description="Translation options")


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