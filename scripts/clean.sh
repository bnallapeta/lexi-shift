#!/bin/bash
# Script to clean up the project

set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Remove build artifacts
rm -rf .build
mkdir -p .build

# Remove Python cache files
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*.pyd" -delete
find . -name ".pytest_cache" -type d -exec rm -rf {} +
find . -name ".coverage" -delete
find . -name "htmlcov" -type d -exec rm -rf {} +

# Remove temporary files
rm -rf /tmp/nllb_models

echo "Project cleaned successfully!" 