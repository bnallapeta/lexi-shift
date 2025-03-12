"""
Tests for the main application module.

This module contains tests for the main FastAPI application.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from src.main import app, lifespan, add_request_id_middleware, global_exception_handler


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_lifespan():
    """Test lifespan context manager."""
    # Create a mock FastAPI app
    mock_app = MagicMock()
    
    # Create a mock for get_model
    with patch('src.main.get_model') as mock_get_model, \
         patch('src.main.logger') as mock_logger:
        
        # Create an async context manager
        async def test_lifespan_context():
            async with lifespan(mock_app):
                # Check that startup actions were performed
                mock_logger.info.assert_any_call("Starting Translation Service", version="0.0.1")
                mock_logger.info.assert_any_call("Initializing translation model")
                mock_get_model.assert_called_once()
                mock_logger.info.assert_any_call("Translation model initialized successfully")
                
                # Yield to simulate the application running
                yield
            
            # Check that shutdown actions were performed
            mock_logger.info.assert_any_call("Shutting down Translation Service")
        
        # Run the test
        import asyncio
        asyncio.run(test_lifespan_context().__anext__())


def test_add_request_id_middleware():
    """Test request ID middleware."""
    # Create mock request and response
    mock_request = MagicMock()
    mock_response = MagicMock()
    mock_response.headers = {}
    
    # Create mock call_next function
    async def mock_call_next(request):
        return mock_response
    
    # Run the middleware
    import asyncio
    asyncio.run(add_request_id_middleware(mock_request, mock_call_next))
    
    # Check that timing header was added
    assert "X-Process-Time" in mock_response.headers


def test_global_exception_handler():
    """Test global exception handler."""
    # Create mock request
    mock_request = MagicMock()
    mock_request.url.path = "/test"
    
    # Create exception
    test_exception = ValueError("Test error")
    
    # Run the exception handler
    with patch('src.main.logger') as mock_logger:
        import asyncio
        response = asyncio.run(global_exception_handler(mock_request, test_exception))
        
        # Check that the error was logged
        mock_logger.error.assert_called_once()
        
        # Check response
        assert response.status_code == 500
        assert "Test error" in response.body.decode()


def test_app_routes(client):
    """Test that the app has the expected routes."""
    routes = [route.path for route in app.routes]
    
    # Check health endpoints
    assert "/health" in routes
    assert "/ready" in routes
    assert "/live" in routes
    
    # Check API endpoints
    assert "/config" in routes
    assert "/translate" in routes
    assert "/batch_translate" in routes 