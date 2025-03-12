"""
Configuration module for the Translation Service.

This module contains settings for the application, including model configuration,
server settings, and logging configuration.
"""

import os
from typing import Dict, List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseSettings):
    """Configuration for the NLLB-200 translation model."""
    model_config = SettingsConfigDict(env_prefix="MODEL_")

    model_size: str = Field(default="small", description="NLLB model size")
    device: str = Field(default="cpu", description="Device to use")
    compute_type: str = Field(default="float32", description="Compute type")
    cpu_threads: int = Field(default=4, ge=1, description="Number of CPU threads")
    num_workers: int = Field(default=1, ge=1, description="Number of workers")
    download_root: str = Field(default="/tmp/nllb_models", description="Root directory for model downloads")
    
    @field_validator("model_size")
    @classmethod
    def validate_model(cls, v: str) -> str:
        valid_sizes = ["small", "medium", "large", "xl"]
        if v not in valid_sizes:
            raise ValueError(f"Invalid model size: {v}. Must be one of {valid_sizes}")
        return v
    
    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        valid_devices = ["cpu", "cuda", "mps"]
        if v not in valid_devices:
            raise ValueError(f"Invalid device: {v}. Must be one of {valid_devices}")
        return v
    
    @field_validator("compute_type")
    @classmethod
    def validate_compute_type(cls, v: str) -> str:
        valid_types = ["int8", "float16", "float32"]
        if v not in valid_types:
            raise ValueError(f"Invalid compute type: {v}. Must be one of {valid_types}")
        return v


class ServerConfig(BaseSettings):
    """Configuration for the FastAPI server."""
    model_config = SettingsConfigDict(env_prefix="SERVER_")

    host: str = Field(default="0.0.0.0", description="Host to bind the server to")
    port: int = Field(default=8000, description="Port to bind the server to")
    workers: int = Field(default=1, description="Number of worker processes")
    log_level: str = Field(default="info", description="Log level")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.lower()


class Settings(BaseSettings):
    """Main settings for the Translation Service."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    app_name: str = Field(default="translation-service", description="Application name")
    app_version: str = Field(default="0.0.1", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    model: ModelConfig = Field(default_factory=ModelConfig, description="Model configuration")
    server: ServerConfig = Field(default_factory=ServerConfig, description="Server configuration")


# Create global settings instance
settings = Settings() 