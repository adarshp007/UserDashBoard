@echo off
REM Development Environment Setup Script for Windows
REM This script sets up the development environment with code quality tools

echo 🚀 Setting up development environment...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

REM Show Python version
echo 📍 Python version:
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install development dependencies
echo 📚 Installing development dependencies...
pip install -r requirements-dev.txt

REM Install pre-commit hooks
echo 🪝 Installing pre-commit hooks...
pre-commit install

REM Run initial checks
echo 🔍 Running initial code quality checks...

REM Format code
echo ✨ Formatting code with black...
black . 2>nul || echo ⚠️  Black formatting had issues (this is normal for first run)

echo 📋 Sorting imports with isort...
isort . 2>nul || echo ⚠️  isort had issues (this is normal for first run)

REM Run Django checks
echo 🔧 Running Django checks...
python manage.py check 2>nul || echo ⚠️  Django checks had issues

REM Check for migrations
echo 🗃️  Checking for missing migrations...
python manage.py makemigrations --check --dry-run 2>nul || echo ⚠️  There might be missing migrations

echo.
echo ✅ Development environment setup complete!
echo.
echo 📋 Available commands:
echo   make help          - Show all available commands
echo   make lint          - Run all linting tools
echo   make format        - Format code
echo   make check         - Run all checks
echo   make test          - Run tests
echo   make pre-commit    - Run pre-commit hooks
echo.
echo 🔧 To activate the virtual environment:
echo   venv\Scripts\activate.bat
echo.
echo 🚀 To start the development server:
echo   python manage.py runserver
echo.
echo 📝 Pre-commit hooks are now installed and will run automatically on git commits.
echo    To run them manually: pre-commit run --all-files

pause
