"""
Tests for the logging setup module.

This module contains tests for the logging configuration.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock

import structlog

from src.logging_setup import setup_logging
from src.config import settings


def test_setup_logging_debug_mode():
    """Test logging setup in debug mode."""
    with patch('src.config.settings.debug', True), \
         patch('structlog.configure') as mock_configure, \
         patch('logging.basicConfig') as mock_basic_config, \
         patch('logging.getLogger') as mock_get_logger:
        
        # Mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Call setup_logging
        setup_logging()
        
        # Check that basicConfig was called
        mock_basic_config.assert_called_once()
        
        # Check that structlog.configure was called
        mock_configure.assert_called_once()
        
        # Check that the loggers were configured
        assert mock_get_logger.call_count == 3
        mock_get_logger.assert_any_call("uvicorn")
        mock_get_logger.assert_any_call("uvicorn.error")
        mock_get_logger.assert_any_call("fastapi")
        
        # Check that the log level was set
        for call in mock_logger.setLevel.call_args_list:
            args, kwargs = call
            assert args[0] == getattr(logging, settings.server.log_level.upper())


def test_setup_logging_production_mode():
    """Test logging setup in production mode."""
    with patch('src.config.settings.debug', False), \
         patch('structlog.configure') as mock_configure, \
         patch('logging.basicConfig') as mock_basic_config, \
         patch('logging.getLogger') as mock_get_logger:
        
        # Mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Call setup_logging
        setup_logging()
        
        # Check that basicConfig was called
        mock_basic_config.assert_called_once()
        
        # Check that structlog.configure was called
        mock_configure.assert_called_once()
        
        # Check that the loggers were configured
        assert mock_get_logger.call_count == 3
        
        # Check that the log level was set
        for call in mock_logger.setLevel.call_args_list:
            args, kwargs = call
            assert args[0] == getattr(logging, settings.server.log_level.upper()) 