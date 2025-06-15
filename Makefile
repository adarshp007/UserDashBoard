.PHONY: help install install-dev lint format check test clean pre-commit setup-dev

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  setup-dev    - Setup development environment (install deps + pre-commit)"
	@echo "  lint         - Run all linting tools"
	@echo "  format       - Format code with black and isort"
	@echo "  check        - Run all checks (lint + Django checks)"
	@echo "  test         - Run tests"
	@echo "  pre-commit   - Install and run pre-commit hooks"
	@echo "  clean        - Clean up cache files"

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

setup-dev: install-dev
	pre-commit install
	@echo "Development environment setup complete!"
	@echo "Pre-commit hooks installed."

# Code quality targets
lint:
	@echo "Running pylint..."
	pylint Account Dashboard utils userdashboard --rcfile=.pylintrc
	@echo "Running flake8..."
	flake8 .
	@echo "Running bandit..."
	bandit -r . -x tests/,test_*.py,*_test.py
	@echo "Running mypy..."
	mypy Account Dashboard utils userdashboard
	@echo "Running pydocstyle..."
	pydocstyle Account Dashboard utils userdashboard

format:
	@echo "Formatting code with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .

check: lint
	@echo "Running Django checks..."
	python manage.py check
	@echo "Checking for missing migrations..."
	python manage.py makemigrations --check --dry-run

# Testing
test:
	@echo "Running tests..."
	python manage.py test

# Pre-commit
pre-commit:
	pre-commit install
	pre-commit run --all-files

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Docker-specific targets
docker-lint:
	docker-compose exec web make lint

docker-format:
	docker-compose exec web make format

docker-check:
	docker-compose exec web make check

docker-test:
	docker-compose exec web make test

# Development server
runserver:
	python manage.py runserver

# Database operations
migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

# Collect static files
collectstatic:
	python manage.py collectstatic --noinput

# Create superuser
createsuperuser:
	python manage.py createsuperuser
