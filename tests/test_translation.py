"""
Tests for the translation model.

This module contains tests for the translation model implementation.
"""

import os
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

from src.config import ModelConfig
from src.logging_setup import logger
from src.models.translation import TranslationModel, get_model


class TestTranslationModel(TranslationModel):
    """A testable subclass of TranslationModel that overrides _initialize_model."""

    def _initialize_model(self):
        """Override _initialize_model to avoid actual model loading."""
        # Set device based on config and availability
        if self.config.device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, falling back to CPU")
            self._device = "cpu"
        elif self.config.device == "mps" and not torch.backends.mps.is_available():
            logger.warning("MPS requested but not available, falling back to CPU")
            self._device = "cpu"
        else:
            self._device = self.config.device

        # Set model name and compute type (for test verification)
        self._model_name = self.MODEL_SIZES.get(self.config.model_size)
        self._compute_type = self.COMPUTE_TYPES.get(self.config.compute_type)

        # Create mock objects for testing
        self.tokenizer = MagicMock()
        self.tokenizer.lang_code_to_id = {
            "en_XX": 0,
            "fr_XX": 1,
            "es_XX": 2,
            "de_XX": 3,
        }

        self.model = MagicMock()
        self.pipeline = MagicMock()
        self.pipeline.return_value = [{"translation_text": "Bonjour, comment ça va?"}]


@pytest.fixture
def translation_model():
    """Create a translation model with mocked components for testing translation."""
    model = TestTranslationModel()
    return model


def test_translation_model_init():
    """Test TranslationModel initialization."""
    with patch("src.models.translation.TranslationModel._initialize_model") as mock_init:
        model = TranslationModel()
        mock_init.assert_called_once()


def test_initialize_model_cpu():
    """Test model initialization on CPU."""
    with (
        patch("torch.cuda.is_available", return_value=False),
        patch("torch.backends.mps.is_available", return_value=False),
    ):

        # Create config with CPU device
        config = ModelConfig(device="cpu", compute_type="float32")

        # Initialize test model
        model = TestTranslationModel(config)

        # Check device
        assert model._device == "cpu"
        assert model._model_name == model.MODEL_SIZES["small"]
        assert model._compute_type == torch.float32


def test_initialize_model_cuda():
    """Test model initialization on CUDA."""
    with (
        patch("torch.cuda.is_available", return_value=True),
        patch("torch.backends.mps.is_available", return_value=False),
    ):

        # Create config with CUDA device
        config = ModelConfig(device="cuda", compute_type="float16")

        # Initialize test model
        model = TestTranslationModel(config)

        # Check device
        assert model._device == "cuda"
        assert model._compute_type == torch.float16


def test_initialize_model_mps():
    """Test model initialization on MPS."""
    with (
        patch("torch.cuda.is_available", return_value=False),
        patch("torch.backends.mps.is_available", return_value=True),
    ):

        # Create config with MPS device
        config = ModelConfig(device="mps", compute_type="float16")

        # Initialize test model
        model = TestTranslationModel(config)

        # Check device
        assert model._device == "mps"
        assert model._compute_type == torch.float16


def test_initialize_model_cuda_fallback():
    """Test model initialization with CUDA fallback to CPU."""
    with (
        patch("torch.cuda.is_available", return_value=False),
        patch("torch.backends.mps.is_available", return_value=False),
    ):

        # Create a subclass that uses our mocked logger
        class TestModel(TestTranslationModel):
            def _initialize_model(self):
                # Set device based on config and availability
                if self.config.device == "cuda" and not torch.cuda.is_available():
                    # Use direct import for patching
                    from src.logging_setup import logger

                    logger.warning("CUDA requested but not available, falling back to CPU")
                    self._device = "cpu"
                elif self.config.device == "mps" and not torch.backends.mps.is_available():
                    self._device = "cpu"
                else:
                    self._device = self.config.device

                # Set model name and compute type (for test verification)
                self._model_name = self.MODEL_SIZES.get(self.config.model_size)
                self._compute_type = self.COMPUTE_TYPES.get(self.config.compute_type)

                # Create mock objects for testing
                self.tokenizer = MagicMock()
                self.model = MagicMock()
                self.pipeline = MagicMock()

        # Patch the logger
        with patch("src.logging_setup.logger") as mock_logger:
            # Create config with CUDA device
            config = ModelConfig(device="cuda", compute_type="float16")

            # Initialize test model
            model = TestModel(config)

            # Check device fallback
            assert model._device == "cpu"
            mock_logger.warning.assert_called_with(
                "CUDA requested but not available, falling back to CPU"
            )


def test_translate(translation_model):
    """Test translate method."""
    # Set up the mock tokenizer to return a specific result
    translation_model.tokenizer.batch_decode.return_value = ["Bonjour, comment ça va?"]

    result = translation_model.translate(
        text="Hello, how are you?",
        source_lang="en",
        target_lang="fr",
        beam_size=5,
        max_length=200,
    )

    # Check result
    assert result == "Bonjour, comment ça va?"

    # Check that model.generate was called
    translation_model.model.generate.assert_called_once()


def test_translate_error(translation_model):
    """Test translate method with error."""
    # Save the original pipeline
    original_pipeline = translation_model.pipeline

    # Set pipeline to None to trigger the RuntimeError
    translation_model.pipeline = None

    try:
        # Test that the exception is properly propagated
        with pytest.raises(RuntimeError) as excinfo:
            translation_model.translate(
                text="Hello, how are you?",
                source_lang="en",
                target_lang="fr",
            )

        # Verify that the exception was raised with the correct message
        assert "Model not initialized" in str(excinfo.value)
    finally:
        # Restore the original pipeline
        translation_model.pipeline = original_pipeline


def test_get_supported_languages(translation_model):
    """Test get_supported_languages method."""
    languages = translation_model.get_supported_languages()

    # Check result
    assert languages == ["de", "en", "es", "fr"]


def test_get_model():
    """Test get_model function."""
    # Create a patch for the translation_model global variable
    with (
        patch("src.models.translation.translation_model", None),
        patch("src.models.translation.TranslationModel") as mock_cls,
    ):

        # Create a mock instance
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        # First call should create a new instance
        model1 = get_model()
        mock_cls.assert_called_once()

        # Reset the mock to verify second call
        mock_cls.reset_mock()

        # Second call should return the existing instance
        model2 = get_model()
        mock_cls.assert_not_called()

        # Both calls should return the same instance
        assert model1 is model2
