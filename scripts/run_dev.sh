#!/bin/bash
# Script to run the service with hot reloading for development

set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create model cache directory if it doesn't exist
mkdir -p /tmp/nllb_models

# Set environment variables for development
export DEBUG=true
export SERVER_LOG_LEVEL=debug

# Run the service with hot reloading
echo "Starting Translation Service in development mode..."
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi 