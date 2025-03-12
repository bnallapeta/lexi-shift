#!/bin/bash
# Script to run tests with coverage

set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests with coverage
python -m pytest --cov=src tests/ "$@"

# Generate HTML coverage report
python -m pytest --cov=src --cov-report=html tests/

echo "Tests completed. Coverage report available in .build/htmlcov/"

# Move coverage data to .build directory
mkdir -p .build
mv .coverage .build/
mv htmlcov .build/

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi 