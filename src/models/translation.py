"""
Translation model implementation using NLLB-200.

This module provides the core functionality for loading and using the NLLB-200 model
for text translation between different languages.
"""

import os
from typing import Dict, List, Optional, Union

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

from src.config import ModelConfig, settings
from src.logging_setup import logger


class TranslationModel:
    """
    Translation model using NLLB-200.
    
    This class handles loading the model, tokenizer, and provides methods for
    translating text between different languages.
    """
    
    # Map model size to HuggingFace model name
    MODEL_SIZES = {
        "small": "facebook/nllb-200-distilled-600M",
        "medium": "facebook/nllb-200-1.3B",
        "large": "facebook/nllb-200-3.3B",
        "xl": "facebook/nllb-200-distilled-1.3B",
    }
    
    # Map compute type to torch dtype
    COMPUTE_TYPES = {
        "int8": torch.int8,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    
    def __init__(self, config: Optional[ModelConfig] = None):
        """
        Initialize the translation model.
        
        Args:
            config: Model configuration. If None, uses the global settings.
        """
        self.config = config or settings.model
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self._device = None
        self._model_name = None
        self._compute_type = None
        
        # Initialize the model
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize the model, tokenizer, and pipeline."""
        try:
            # Set device
            if self.config.device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available, falling back to CPU")
                self._device = "cpu"
            elif self.config.device == "mps" and not torch.backends.mps.is_available():
                logger.warning("MPS requested but not available, falling back to CPU")
                self._device = "cpu"
            else:
                self._device = self.config.device
            
            # Set model name
            self._model_name = self.MODEL_SIZES.get(self.config.model_size)
            if not self._model_name:
                raise ValueError(f"Invalid model size: {self.config.model_size}")
            
            # Set compute type
            self._compute_type = self.COMPUTE_TYPES.get(self.config.compute_type)
            if not self._compute_type:
                raise ValueError(f"Invalid compute type: {self.config.compute_type}")
            
            # Create cache directory if it doesn't exist
            os.makedirs(self.config.download_root, exist_ok=True)
            
            # Log model loading
            logger.info(
                "Loading NLLB-200 model",
                model_name=self._model_name,
                device=self._device,
                compute_type=self.config.compute_type,
            )
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self._model_name,
                cache_dir=self.config.download_root,
            )
            
            # Load model with appropriate settings
            # Only use low_cpu_mem_usage if accelerate is available
            try:
                import accelerate
                use_low_cpu_mem = True
            except ImportError:
                use_low_cpu_mem = False
                logger.warning("Accelerate not available, disabling low_cpu_mem_usage")
            
            # Determine if we should use int8 quantization
            use_int8 = self._compute_type == torch.int8 and self._device == "cpu"
            
            # For int8, we'll use 8-bit loading instead of post-loading quantization
            if use_int8:
                try:
                    import bitsandbytes as bnb
                    logger.info("Using bitsandbytes for 8-bit quantization")
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(
                        self._model_name,
                        cache_dir=self.config.download_root,
                        device_map=self._device if use_low_cpu_mem else None,
                        load_in_8bit=True,
                        low_cpu_mem_usage=use_low_cpu_mem,
                    )
                except ImportError:
                    logger.warning("bitsandbytes not available, falling back to float32")
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(
                        self._model_name,
                        cache_dir=self.config.download_root,
                        device_map=self._device if use_low_cpu_mem else None,
                        torch_dtype=torch.float32,
                        low_cpu_mem_usage=use_low_cpu_mem,
                    )
            else:
                # Load with specified compute type (float16 or float32)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    self._model_name,
                    cache_dir=self.config.download_root,
                    device_map=self._device if use_low_cpu_mem else None,
                    torch_dtype=self._compute_type if self._compute_type != torch.int8 else torch.float32,
                    low_cpu_mem_usage=use_low_cpu_mem,
                )
            
            # Move model to device if not using device_map
            if not use_low_cpu_mem and not use_int8:
                if self._device == "cuda":
                    self.model = self.model.cuda()
                elif self._device == "mps":
                    self.model = self.model.to("mps")
            
            # Create translation pipeline
            self.pipeline = pipeline(
                task="translation",
                model=self.model,
                tokenizer=self.tokenizer,
                # Don't specify device when using accelerate or int8
                device=None,  # Always set to None to avoid conflicts with accelerate
            )
            
            logger.info("Model loaded successfully")
        
        except Exception as e:
            logger.error("Failed to initialize model", error=str(e), exc_info=True)
            raise
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        beam_size: int = 5,
        max_length: int = 200,
    ) -> str:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            beam_size: Beam size for beam search
            max_length: Maximum output length
            
        Returns:
            Translated text
        """
        if not self.pipeline:
            raise RuntimeError("Model not initialized")
        
        # Convert ISO language codes to NLLB language codes
        src_lang_code = self.get_nllb_language_code(source_lang)
        tgt_lang_code = self.get_nllb_language_code(target_lang)
        
        try:
            logger.debug(
                "Translating text",
                source_lang=source_lang,
                target_lang=target_lang,
                text_length=len(text),
                src_lang_code=src_lang_code,
                tgt_lang_code=tgt_lang_code,
            )
            
            # Check if language codes are valid
            if src_lang_code not in self.tokenizer.lang_code_to_id:
                logger.warning(f"Source language code {src_lang_code} not found in tokenizer")
                valid_codes = list(self.tokenizer.lang_code_to_id.keys())[:10]
                logger.warning(f"Valid language codes (first 10): {valid_codes}")
                src_lang_code = "eng_XX"  # Default to English
            
            if tgt_lang_code not in self.tokenizer.lang_code_to_id:
                logger.warning(f"Target language code {tgt_lang_code} not found in tokenizer")
                valid_codes = list(self.tokenizer.lang_code_to_id.keys())[:10]
                logger.warning(f"Valid language codes (first 10): {valid_codes}")
                tgt_lang_code = "fra_XX"  # Default to French
            
            # For NLLB-200, we need to use the forced_bos_token_id parameter
            # to specify the target language
            forced_bos_token_id = self.tokenizer.lang_code_to_id.get(tgt_lang_code)
            logger.debug(f"Forced BOS token ID: {forced_bos_token_id} for language {tgt_lang_code}")
            
            # Set the source language in the tokenizer
            self.tokenizer.src_lang = src_lang_code
            
            # Generate translation
            inputs = self.tokenizer(text, return_tensors="pt")
            
            # Move inputs to the same device as the model
            if hasattr(self.model, "device"):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate translation
            outputs = self.model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=max_length,
                num_beams=beam_size,
                early_stopping=True,
            )
            
            # Decode the generated tokens
            translated_text = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            
            logger.debug("Translation result", translated_text=translated_text)
            
            logger.debug(
                "Translation completed",
                source_lang=source_lang,
                target_lang=target_lang,
                result_length=len(translated_text),
                translated_text=translated_text,
            )
            
            return translated_text
        
        except Exception as e:
            logger.error(
                "Translation failed",
                error=str(e),
                source_lang=source_lang,
                target_lang=target_lang,
                exc_info=True,
            )
            raise
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.
        
        Returns:
            List of supported language codes
        """
        if not self.tokenizer:
            raise RuntimeError("Model not initialized")
        
        # Extract language codes from tokenizer
        lang_codes = []
        for code in self.tokenizer.lang_code_to_id:
            # Map NLLB language codes to ISO codes
            parts = code.split('_')
            if len(parts) >= 2:
                nllb_code = parts[0]
                # Common language code mappings
                nllb_to_iso = {
                    "eng": "en",
                    "fra": "fr",
                    "deu": "de",
                    "spa": "es",
                    "ita": "it",
                    "por": "pt",
                    "rus": "ru",
                    "zho": "zh",
                    "jpn": "ja",
                    "kor": "ko",
                    "ara": "ar",
                    "hin": "hi",
                }
                iso_code = nllb_to_iso.get(nllb_code, nllb_code)
                lang_codes.append(iso_code)
        
        return sorted(lang_codes)
    
    def get_nllb_language_code(self, iso_code: str) -> str:
        """
        Convert ISO language code to NLLB language code.
        
        Args:
            iso_code: ISO language code (e.g., 'en', 'fr')
            
        Returns:
            NLLB language code (e.g., 'eng_Latn', 'fra_Latn')
        """
        # Common ISO to NLLB language code mappings
        iso_to_nllb = {
            "en": "eng_Latn",
            "fr": "fra_Latn",
            "de": "deu_Latn",
            "es": "spa_Latn",
            "it": "ita_Latn",
            "pt": "por_Latn",
            "ru": "rus_Cyrl",
            "zh": "zho_Hans",
            "ja": "jpn_Jpan",
            "ko": "kor_Hang",
            "ar": "ara_Arab",
            "hi": "hin_Deva",
        }
        
        # If the ISO code is not in our mapping, try to find a matching code in the tokenizer
        if iso_code not in iso_to_nllb:
            for code in self.tokenizer.lang_code_to_id:
                if code.startswith(iso_code + "_"):
                    return code
        
        return iso_to_nllb.get(iso_code, iso_code)


# Create a global model instance
translation_model = None


def get_model() -> TranslationModel:
    """
    Get or create the global translation model instance.
    
    Returns:
        TranslationModel instance
    """
    global translation_model
    
    if translation_model is None:
        translation_model = TranslationModel()
    
    return translation_model 