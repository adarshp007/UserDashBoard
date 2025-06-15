#!/bin/bash

# Development Environment Setup Script
# This script sets up the development environment with code quality tools

set -e  # Exit on any error

echo "🚀 Setting up development environment..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "📍 Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "📚 Installing development dependencies..."
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install

# Run initial checks
echo "🔍 Running initial code quality checks..."

# Format code
echo "✨ Formatting code with black..."
black . || echo "⚠️  Black formatting had issues (this is normal for first run)"

echo "📋 Sorting imports with isort..."
isort . || echo "⚠️  isort had issues (this is normal for first run)"

# Run Django checks
echo "🔧 Running Django checks..."
python manage.py check || echo "⚠️  Django checks had issues"

# Check for migrations
echo "🗃️  Checking for missing migrations..."
python manage.py makemigrations --check --dry-run || echo "⚠️  There might be missing migrations"

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Available commands:"
echo "  make help          - Show all available commands"
echo "  make lint          - Run all linting tools"
echo "  make format        - Format code"
echo "  make check         - Run all checks"
echo "  make test          - Run tests"
echo "  make pre-commit    - Run pre-commit hooks"
echo ""
echo "🔧 To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "🚀 To start the development server:"
echo "  python manage.py runserver"
echo ""
echo "📝 Pre-commit hooks are now installed and will run automatically on git commits."
echo "   To run them manually: pre-commit run --all-files"
