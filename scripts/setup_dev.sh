#!/bin/bash
# Script to set up the development environment

set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black isort flake8 mypy

# Create necessary directories
mkdir -p .build
mkdir -p /tmp/nllb_models

# Create configuration files for code quality tools
if [ ! -f "pyproject.toml" ]; then
    echo "Creating pyproject.toml for black and isort..."
    cat > pyproject.toml << EOF
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
skip_gitignore = true
EOF
fi

if [ ! -f ".flake8" ]; then
    echo "Creating .flake8 configuration..."
    cat > .flake8 << EOF
[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist,venv,.venv
ignore = E203, W503
EOF
fi

# Install git hooks
echo "Installing git hooks..."
./scripts/install_hooks.sh

echo "Development environment set up successfully!"
echo "To activate the virtual environment, run: source venv/bin/activate" 