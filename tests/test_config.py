"""
Tests for the configuration module.

This module contains tests for the configuration classes and validation.
"""

import os

import pytest
from pydantic import ValidationError

from src.config import ModelConfig, ServerConfig, Settings


def test_model_config_defaults():
    """Test ModelConfig default values."""
    config = ModelConfig()
    assert config.model_size == "small"
    assert config.device == "cpu"
    assert config.compute_type == "float32"
    assert config.cpu_threads == 4
    assert config.num_workers == 1
    assert config.download_root == "/tmp/nllb_models"


def test_model_config_validation():
    """Test ModelConfig validation."""
    # Test valid values
    config = ModelConfig(
        model_size="medium",
        device="cuda",
        compute_type="float16",
        cpu_threads=8,
        num_workers=2,
        download_root="/custom/path",
    )
    assert config.model_size == "medium"
    assert config.device == "cuda"
    assert config.compute_type == "float16"
    assert config.cpu_threads == 8
    assert config.num_workers == 2
    assert config.download_root == "/custom/path"

    # Test invalid model_size
    with pytest.raises(ValidationError):
        ModelConfig(model_size="invalid")

    # Test invalid device
    with pytest.raises(ValidationError):
        ModelConfig(device="invalid")

    # Test invalid compute_type
    with pytest.raises(ValidationError):
        ModelConfig(compute_type="invalid")

    # Test invalid cpu_threads
    with pytest.raises(ValidationError):
        ModelConfig(cpu_threads=0)

    # Test invalid num_workers
    with pytest.raises(ValidationError):
        ModelConfig(num_workers=0)


def test_server_config_defaults():
    """Test ServerConfig default values."""
    config = ServerConfig()
    assert config.host == "0.0.0.0"
    assert config.port == 8000
    assert config.workers == 1
    assert config.log_level == "info"
    assert config.cors_origins == ["*"]


def test_server_config_validation():
    """Test ServerConfig validation."""
    # Test valid values
    config = ServerConfig(
        host="127.0.0.1",
        port=9000,
        workers=4,
        log_level="debug",
        cors_origins=["http://localhost:3000", "https://example.com"],
    )
    assert config.host == "127.0.0.1"
    assert config.port == 9000
    assert config.workers == 4
    assert config.log_level == "debug"
    assert config.cors_origins == ["http://localhost:3000", "https://example.com"]

    # Test invalid log_level
    with pytest.raises(ValidationError):
        ServerConfig(log_level="invalid")


def test_settings_defaults():
    """Test Settings default values."""
    config = Settings()
    assert config.app_name == "translation-service"
    assert config.app_version == "0.0.1"
    assert config.debug is False
    assert isinstance(config.model, ModelConfig)
    assert isinstance(config.server, ServerConfig)


def test_settings_from_env(monkeypatch):
    """Test Settings from environment variables."""
    # Set environment variables
    monkeypatch.setenv("APP_NAME", "custom-service")
    monkeypatch.setenv("APP_VERSION", "1.0.0")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("MODEL__MODEL_SIZE", "large")
    monkeypatch.setenv("SERVER__PORT", "9000")

    # Create settings
    config = Settings()

    # Check values
    assert config.app_name == "custom-service"
    assert config.app_version == "1.0.0"
    assert config.debug is True
    assert config.model.model_size == "large"
    assert config.server.port == 9000
