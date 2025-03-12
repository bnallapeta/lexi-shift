#!/bin/bash
# Script to install git hooks

set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook to ensure code quality

set -e

# Get the list of staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo "No Python files staged for commit. Skipping code quality checks."
    exit 0
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if the required tools are installed
if ! command -v black &> /dev/null || ! command -v isort &> /dev/null || ! command -v flake8 &> /dev/null; then
    echo "Error: black, isort, or flake8 not found. Please run ./scripts/setup_dev.sh to install them."
    exit 1
fi

# Format and lint the staged files
echo "Running code quality checks on staged files..."

# Format with black
echo "Formatting with black..."
black $STAGED_FILES

# Format with isort
echo "Formatting with isort..."
isort $STAGED_FILES

# Lint with flake8
echo "Linting with flake8..."
flake8 $STAGED_FILES

# Add the formatted files back to the staging area
git add $STAGED_FILES

echo "Code quality checks passed!"
exit 0
EOF

# Make the hook executable
chmod +x .git/hooks/pre-commit

echo "Git hooks installed successfully!" 