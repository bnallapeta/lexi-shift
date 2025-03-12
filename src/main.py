"""
Main application module for the Translation Service.

This module initializes the FastAPI application and sets up middleware,
routes, and exception handlers.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src import __version__
from src.api.endpoints import router as api_router
from src.config import settings
from src.logging_setup import logger, setup_logging
from src.models.translation import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    
    This handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Translation Service", version=__version__)
    
    # Initialize model on startup
    try:
        logger.info("Initializing translation model")
        get_model()
        logger.info("Translation model initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize translation model", error=str(e), exc_info=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Translation Service")


# Set up logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="Translation Service",
    description="A high-performance text translation service using NLLB-200 models.",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """
    Middleware to add request ID and timing information.
    """
    # Start timer
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate request duration
    duration = time.time() - start_time
    
    # Add timing header
    response.headers["X-Process-Time"] = str(duration)
    
    return response

# Add exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "error_type": type(exc).__name__,
        },
    )

# Include API router
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.server.host,
        port=settings.server.port,
        log_level=settings.server.log_level,
        reload=settings.debug,
    ) 