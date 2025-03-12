"""
Tests for the language detection feature.

This module contains tests for the language detection functionality.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.models.translation import TranslationModel


class TestLanguageDetectionModel(TranslationModel):
    """A testable subclass of TranslationModel that overrides _initialize_model."""

    def _initialize_model(self):
        """Override _initialize_model to avoid actual model loading."""
        self._device = "cpu"
        self._model_name = self.MODEL_SIZES.get(self.config.model_size)
        self._compute_type = self.COMPUTE_TYPES.get(self.config.compute_type)

        # Create mock objects for testing
        self.tokenizer = MagicMock()
        self.tokenizer.lang_code_to_id = {
            "eng_Latn": 0,
            "fra_Latn": 1,
            "spa_Latn": 2,
            "deu_Latn": 3,
            "rus_Cyrl": 4,
            "zho_Hans": 5,
        }

        # Mock encode method to return different token lengths based on language
        def mock_encode(text, add_special_tokens=True):
            # Return different token lengths based on the source language
            # to simulate language detection
            if self.tokenizer.src_lang == "eng_Latn":
                return [1, 2, 3]  # 3 tokens for English
            elif self.tokenizer.src_lang == "fra_Latn":
                return [1, 2, 3, 4, 5]  # 5 tokens for French
            elif self.tokenizer.src_lang == "spa_Latn":
                return [1, 2, 3, 4]  # 4 tokens for Spanish
            elif self.tokenizer.src_lang == "deu_Latn":
                return [1, 2, 3, 4, 5, 6]  # 6 tokens for German
            else:
                return [1, 2, 3, 4, 5, 6, 7, 8]  # 8 tokens for other languages

        self.tokenizer.encode = mock_encode

        self.model = MagicMock()
        self.pipeline = MagicMock()


@pytest.fixture
def detection_model():
    """Create a translation model with mocked components for testing language detection."""
    model = TestLanguageDetectionModel()
    return model


def test_detect_language(detection_model):
    """Test detect_language method."""
    # Test with default parameters
    detections = detection_model.detect_language("Hello, how are you?")

    # Should return a list with one detection
    assert isinstance(detections, list)
    assert len(detections) == 1

    # The detection should have language and confidence
    detection = detections[0]
    assert "language" in detection
    assert "confidence" in detection

    # The language with the highest score (shortest token length) should be English
    assert detection["language"] == "en"

    # Test with top_k=3
    detections = detection_model.detect_language("Hello, how are you?", top_k=3)

    # Should return a list with three detections
    assert isinstance(detections, list)
    assert len(detections) == 3

    # The detections should be sorted by confidence (highest first)
    assert detections[0]["confidence"] >= detections[1]["confidence"]
    assert detections[1]["confidence"] >= detections[2]["confidence"]


def test_detect_language_error(detection_model):
    """Test detect_language method with error."""
    # Patch the logger to avoid logging the error
    with patch("src.logging_setup.logger"):
        # Make the tokenizer raise an exception when encode is called
        # We need to patch the specific instance's encode method
        detection_model.tokenizer.encode.side_effect = Exception("Tokenization error")

        # Also patch the src_lang property to raise an exception when accessed
        type(detection_model.tokenizer).src_lang = property(
            lambda self: self._src_lang,
            lambda self, value: exec('raise Exception("Tokenization error")'),
        )

        # Now the test should raise an exception
        with pytest.raises(Exception) as excinfo:
            detection_model.detect_language("Hello, how are you?")

        assert "Tokenization error" in str(excinfo.value)


def test_detect_language_empty_text(detection_model):
    """Test detect_language method with empty text."""
    detections = detection_model.detect_language("")

    # Should still return a list with one detection
    assert isinstance(detections, list)
    assert len(detections) == 1
