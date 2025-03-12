"""
Cache module for the Translation Service.

This module provides a simple in-memory cache for translations.
"""

import time
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Union

from src.logging_setup import logger


class TranslationCache:
    """Simple in-memory cache for translations."""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of items in the cache
            ttl: Time to live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[str]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp <= self.ttl:
                self.hits += 1
                return value
            else:
                # Remove expired item
                del self.cache[key]

        self.misses += 1
        return None

    def set(self, key: str, value: str) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        # If cache is full, remove oldest item
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
            del self.cache[oldest_key]

        self.cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        logger.info("Translation cache cleared")

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
        }


# Create global cache instance
translation_cache = TranslationCache()


def generate_cache_key(
    text: str, source_lang: str, target_lang: str, beam_size: int, max_length: int
) -> str:
    """
    Generate a cache key for a translation.

    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        beam_size: Beam size
        max_length: Maximum output length

    Returns:
        Cache key
    """
    return f"{source_lang}:{target_lang}:{beam_size}:{max_length}:{text}"
