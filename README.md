# User Dashboard

A Django application for managing user dashboards with advanced data visualization and aggregation capabilities. This application allows users to upload, process, and visualize datasets through an intuitive web interface.

## Table of Contents

- [Features](#features)
- [Docker Setup](#docker-setup)
- [API Endpoints](#api-endpoints)
- [Development](#development)
  - [Quick Development Setup](#quick-development-setup)
  - [Manual Development Setup](#manual-development-setup)
  - [Code Quality Tools](#code-quality-tools)
  - [Pre-commit Hooks](#pre-commit-hooks)
  - [Development Workflow](#development-workflow)
  - [Docker Development](#docker-development)
  - [CI/CD Pipeline](#cicd-pipeline)
- [Benefits of Code Quality Tools](#-benefits-of-code-quality-tools)
- [Features Implemented](#-features-implemented)
- [Setup Instructions for New Developers](#-setup-instructions-for-new-developers)
- [Recommended Development Workflow](#-recommended-development-workflow)
- [Security Features](#-security-features)
- [Code Style Guidelines](#-code-style-guidelines)
- [Contributing Guidelines](#contributing-guidelines)
- [Troubleshooting](#-troubleshooting)
- [Tech Stack](#tech-stack)
- [License](#license)

## Features

### Data Management
- Upload and process CSV and Excel (XLSX) files
- Automatic conversion to optimized Parquet format for faster processing
- Background processing of large files using Celery
- Secure file storage using Minio (S3-compatible storage)
- Dataset metadata extraction and storage

### Data Visualization
- Interactive chart generation with multiple chart types (bar, line, pie, scatter)
- Support for single and multiple Y-axis variables
- Customizable aggregation settings for both X and Y axes
- Time-based aggregations for date columns (daily, monthly, quarterly, yearly)
- Filtering capabilities to focus on specific data subsets

### User Interface
- Clean, responsive dashboard interface
- Dataset list view with status indicators
- Detailed dataset view showing columns and available aggregations
- Interactive visualization form with dynamic options based on data types
- Real-time feedback on aggregation selections

## Docker Setup

### Prerequisites

- Docker
- Docker Compose

### Getting Started

1. Clone the repository:
   ```
   git clone <repository-url>
   cd UserDashBoard
   ```

2. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```

3. Update the `.env` file with your configuration values.

4. Build and start the Docker containers:
   ```
   docker-compose up -d --build
   ```

5. Create a superuser (optional):
   ```
   docker-compose exec web python manage.py createsuperuser
   ```

6. Access the application:
   - Web interface: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

### Docker Commands

- Start the containers:
  ```
  docker-compose up -d
  ```

- Stop the containers:
  ```
  docker-compose down
  ```

- View logs:
  ```
  docker-compose logs -f
  ```

- Run Django management commands:
  ```
  docker-compose exec web python manage.py <command>
  ```

## API Endpoints

### Dataset Management
- `POST /dashboard/api/datasets/`: Upload and create a new dataset
- `GET /dashboard/api/datasets/`: List all datasets
- `GET /dashboard/api/datasets/<uuid:dataset_id>/`: Get dataset details
- `DELETE /dashboard/api/datasets/<uuid:dataset_id>/`: Delete a dataset
- `GET /dashboard/api/datasets/<uuid:dataset_id>/status/`: Check the status of a dataset

### Data Analysis
- `POST /dashboard/api/datasets/<uuid:dataset_id>/aggregations/`: Perform aggregations on a dataset
- `GET /dashboard/api/datasets/<uuid:dataset_id>/columns/`: Get available aggregations for each column in a dataset
- `POST /dashboard/api/datasets/<uuid:dataset_id>/visualize/`: Generate visualization data based on selected variables and aggregations

### Web Interface
- `GET /dashboard/datasets/`: View list of all datasets
- `GET /dashboard/datasets/<uuid:dataset_id>/`: View dataset details and visualization interface
- `GET /dashboard/upload/`: Access the file upload interface

## Development

### Quick Development Setup

For a quick setup with all development tools and code quality checks:

**Linux/macOS:**
```bash
./setup-dev.sh
```

**Windows:**
```batch
setup-dev.bat
```

This will:
- Create a virtual environment
- Install all development dependencies
- Set up pre-commit hooks
- Run initial code formatting and checks

### Manual Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

7. Start Celery worker (in a separate terminal):
   ```bash
   celery -A userdashboard worker --loglevel=info
   ```

### Code Quality Tools

This project uses comprehensive code quality tools to maintain high standards and ensure consistent code across all contributors.

#### 🛠️ Tools Included

1. **Code Quality Tools:**
   - **pylint**: Static code analysis (configured with `.pylintrc`)
   - **black**: Code formatter (120 character line length)
   - **isort**: Import statement organizer
   - **flake8**: Style guide enforcement
   - **bandit**: Security vulnerability scanner
   - **mypy**: Static type checker
   - **pydocstyle**: Docstring style checker

2. **Pre-commit Hooks:**
   - Automatic code formatting on commit
   - Linting and security checks
   - Django-specific checks
   - File validation (trailing whitespace, large files, etc.)

3. **Testing Tools:**
   - **pytest**: Modern testing framework
   - **pytest-django**: Django integration for pytest
   - **pytest-cov**: Coverage reporting
   - **factory-boy**: Test data generation

4. **Development Tools:**
   - **ipython**: Enhanced Python shell
   - **django-debug-toolbar**: Debug information
   - **django-extensions**: Additional Django commands

#### 📁 Configuration Files

- **`.pylintrc`**: Comprehensive pylint configuration
- **`.pre-commit-config.yaml`**: Pre-commit hooks configuration
- **`pyproject.toml`**: Tool configurations (black, isort, mypy, etc.)
- **`requirements-dev.txt`**: Development dependencies
- **`Makefile`**: Common development commands
- **`.github/workflows/ci.yml`**: GitHub Actions CI/CD pipeline

#### Available Make Commands

```bash
make help          # Show all available commands
make install       # Install production dependencies
make install-dev   # Install development dependencies
make setup-dev     # Setup complete development environment
make lint          # Run all linting tools
make format        # Format code with black and isort
make check         # Run all checks (lint + Django checks)
make test          # Run tests
make pre-commit    # Install and run pre-commit hooks
make clean         # Clean up cache files
```

#### Docker Commands for Development

```bash
# Install dev dependencies in Docker
docker-compose exec web pip install -r requirements-dev.txt

# Run tools in Docker
docker-compose exec web make lint
docker-compose exec web make format
docker-compose exec web make check
docker-compose exec web make test
```

#### Running Individual Tools

```bash
# Linting
pylint Account Dashboard utils userdashboard --rcfile=.pylintrc
flake8 .
bandit -r . -x tests/,test_*.py,*_test.py

# Type checking
mypy Account Dashboard utils userdashboard

# Code formatting
black .
isort .

# Django checks
python manage.py check
python manage.py makemigrations --check --dry-run
```

#### 📊 Current Code Quality Status

- **Pylint Score**: 9.54/10 (Excellent!)
- **Black**: All files properly formatted
- **isort**: All imports properly organized
- **Security**: No known vulnerabilities detected

### Pre-commit Hooks

Pre-commit hooks are automatically installed and will run on every commit. They include:

- Code formatting (black, isort)
- Linting (pylint, flake8)
- Security checks (bandit)
- Type checking (mypy)
- Django-specific checks
- General file checks (trailing whitespace, large files, etc.)

To run pre-commit hooks manually:
```bash
pre-commit run --all-files
```

### Development Workflow

1. **Before starting work:**
   ```bash
   git checkout -b feature/your-feature-name
   make format  # Format existing code
   ```

2. **During development:**
   - Write code following the project's style guidelines
   - Add tests for new functionality
   - Run `make check` periodically to catch issues early

3. **Before committing:**
   ```bash
   make check  # Run all quality checks
   make test   # Run tests
   git add .
   git commit -m "Your commit message"
   # Pre-commit hooks will run automatically
   ```

4. **Before pushing:**
   ```bash
   make lint   # Final lint check
   git push origin feature/your-feature-name
   ```

### Docker Development

You can also run development commands inside Docker:

```bash
# Run linting in Docker
docker-compose exec web make lint

# Format code in Docker
docker-compose exec web make format

# Run tests in Docker
docker-compose exec web make test
```

### CI/CD Pipeline

The project includes a GitHub Actions workflow that:
- Runs on Python 3.9, 3.10, and 3.11
- Executes all pre-commit hooks
- Runs Django checks and tests
- Performs security scanning
- Builds and tests Docker images

### 🎯 Benefits of Code Quality Tools

1. **Code Quality**: Consistent, high-quality code across the project
2. **Early Error Detection**: Catch issues before they reach production
3. **Team Collaboration**: Standardized code style for all contributors
4. **Security**: Automated security vulnerability scanning
5. **Documentation**: Enforced docstring standards
6. **Maintainability**: Easier to maintain and extend the codebase

### 🔧 Features Implemented

1. **Automatic Code Formatting**: Black and isort ensure consistent code style
2. **Comprehensive Linting**: Multiple tools catch different types of issues
3. **Security Scanning**: Bandit identifies potential security vulnerabilities
4. **Type Checking**: MyPy helps catch type-related errors
5. **Pre-commit Hooks**: Automatic quality checks before commits
6. **CI/CD Pipeline**: GitHub Actions workflow for continuous integration
7. **Django-Specific Checks**: Custom hooks for Django best practices

### 📝 Setup Instructions for New Developers

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd userdashboard
   ```

2. **Quick setup with all tools**:
   ```bash
   # Linux/macOS
   ./setup-dev.sh

   # Windows
   setup-dev.bat

   # Or manually
   make setup-dev
   ```

3. **Install pre-commit hooks** (if not using setup scripts):
   ```bash
   pre-commit install
   ```

4. **Verify setup**:
   ```bash
   make check
   ```

### 🔄 Recommended Development Workflow

1. **Before starting work**:
   ```bash
   git checkout -b feature/your-feature-name
   make format  # Format existing code
   ```

2. **During development**:
   - Write code following the project's style guidelines
   - Add tests for new functionality
   - Run `make check` periodically to catch issues early

3. **Before committing**:
   ```bash
   make check  # Run all quality checks
   make test   # Run tests
   git add .
   git commit -m "Your commit message"
   # Pre-commit hooks will run automatically
   ```

4. **Before pushing**:
   ```bash
   make lint   # Final lint check
   git push origin feature/your-feature-name
   ```

### 🚀 CI/CD Pipeline

The project includes a comprehensive GitHub Actions workflow that:

- **Multi-Python Testing**: Runs on Python 3.9, 3.10, and 3.11
- **Database Testing**: Uses PostgreSQL and Redis services
- **Code Quality Checks**: Executes all pre-commit hooks
- **Security Scanning**: Runs Bandit and Trivy vulnerability scanners
- **Django Validation**: Runs Django checks and migration validation
- **Test Coverage**: Generates and uploads coverage reports
- **Docker Testing**: Builds and tests Docker images
- **Dependency Caching**: Optimized for faster CI runs

### 🛡️ Security Features

- **Bandit**: Scans for common security issues in Python code
- **Trivy**: Vulnerability scanner for dependencies and Docker images
- **Pre-commit hooks**: Detect private keys and sensitive information
- **GitHub Security**: SARIF upload for security findings

### 📋 Code Style Guidelines

- **Line Length**: 120 characters maximum
- **Import Organization**: Grouped and sorted by isort
- **Code Formatting**: Consistent formatting with Black
- **Docstrings**: Google-style docstrings enforced
- **Type Hints**: Encouraged for better code documentation
- **Naming Conventions**: Snake_case for variables and functions, PascalCase for classes

### Contributing Guidelines

1. **Code Style**: Follow the existing code style (enforced by pre-commit hooks)
2. **Testing**: Write tests for new functionality
3. **Documentation**: Update documentation as needed
4. **Quality Checks**: Ensure all CI checks pass
5. **Commit Messages**: Keep commits focused and write clear commit messages
6. **Security**: Run security checks before submitting PRs
7. **Performance**: Consider performance implications of changes

### 🔧 Troubleshooting

#### Common Issues and Solutions

1. **Pre-commit hooks failing**:
   ```bash
   # Update hooks
   pre-commit autoupdate

   # Run hooks manually to see detailed errors
   pre-commit run --all-files

   # Skip hooks temporarily (not recommended)
   git commit --no-verify
   ```

2. **Pylint errors**:
   ```bash
   # Check specific files
   pylint path/to/file.py --rcfile=.pylintrc

   # Generate pylint config
   pylint --generate-rcfile > .pylintrc
   ```

3. **Import errors in development**:
   ```bash
   # Ensure development dependencies are installed
   pip install -r requirements-dev.txt

   # Check Python path
   python -c "import sys; print(sys.path)"
   ```

4. **Docker development issues**:
   ```bash
   # Rebuild containers
   docker-compose down
   docker-compose build --no-cache
   docker-compose up

   # Install dev dependencies in container
   docker-compose exec web pip install -r requirements-dev.txt
   ```

5. **Type checking errors**:
   ```bash
   # Run mypy with verbose output
   mypy --show-error-codes path/to/file.py

   # Ignore specific errors (add to pyproject.toml)
   # type: ignore[error-code]
   ```

#### Performance Tips

- Use `make format` before committing to avoid pre-commit delays
- Run `make check` locally before pushing to catch CI failures early
- Use Docker commands for consistent environment across team members
- Cache pip dependencies in CI for faster builds

#### Getting Help

- Check the [GitHub Issues](https://github.com/your-repo/issues) for known problems
- Review the tool documentation:
  - [Pylint Documentation](https://pylint.pycqa.org/)
  - [Black Documentation](https://black.readthedocs.io/)
  - [Pre-commit Documentation](https://pre-commit.com/)
- Run `make help` for available commands

## Tech Stack

### Backend
- **Django 4.2+**: Web framework
- **Django REST Framework**: API development
- **Celery**: Asynchronous task processing
- **Redis**: Message broker and caching
- **PostgreSQL**: Primary database
- **Polars**: High-performance data processing
- **Minio**: S3-compatible object storage

### Frontend
- **HTML5/CSS3**: Structure and styling
- **JavaScript (ES6+)**: Interactive functionality
- **Chart.js**: Data visualization
- **Bootstrap**: Responsive design framework

### Development & Deployment
- **Docker & Docker Compose**: Containerization
- **GitHub Actions**: CI/CD pipeline
- **Pre-commit**: Code quality automation
- **Pylint, Black, isort**: Code quality tools
- **Bandit, Trivy**: Security scanning
- **MyPy**: Static type checking
- **Pytest**: Testing framework

### Data Processing
- **Polars**: Fast DataFrame operations
- **Parquet**: Optimized data storage format
- **CSV/Excel**: Input file formats
- **Time-series aggregations**: Daily, monthly, quarterly, yearly

### Infrastructure
- **Minio**: File storage (S3-compatible)
- **Redis**: Caching and task queue
- **PostgreSQL**: Relational database
- **Docker**: Containerized deployment

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ❌ Liability
- ❌ Warranty

### Contributing

By contributing to this project, you agree that your contributions will be licensed under the same MIT License.

---

**Built with ❤️ using Django and modern Python tools**

## Using the Visualization Features

### Uploading a Dataset
1. Navigate to the upload page at `/dashboard/upload/`
2. Select a CSV or Excel file from your computer
3. Provide a name and optional description for the dataset
4. Click "Upload" to start the upload and processing
5. The system will automatically extract metadata and identify column types

### Creating Visualizations
1. From the datasets list, click on a dataset to view its details
2. In the visualization section:
   - Select one or more variables for the X-axis
   - Select one or more variables for the Y-axis
   - Choose a chart type (bar, line, pie, scatter)
   - Optionally set filters to focus on specific data

3. Configure aggregation settings:
   - For each X-axis variable, select an appropriate aggregation
   - For each Y-axis variable, select an appropriate aggregation
   - Available aggregations depend on the column type:
     - Numeric columns: sum, mean, min, max, median, etc.
     - Date columns: daily, monthly, quarterly, yearly aggregations
     - String columns: count, first, last, etc.

4. Click "Generate Visualization" to create the chart
5. The visualization will display with a summary of the data and applied aggregations

### Working with Aggregations
- **No Aggregation**: Uses raw data values (with automatic grouping for categorical X-axis)
- **Sum**: Calculates the sum of values for each group
- **Mean**: Calculates the average of values for each group
- **Min/Max**: Shows the minimum or maximum value in each group
- **Count**: Counts the number of occurrences in each group
- **Time-based**: Groups date/time data by the specified period

### Tips for Effective Visualizations
- Choose appropriate chart types for your data:
  - Bar charts: Good for comparing categories
  - Line charts: Best for showing trends over time
  - Pie charts: Useful for showing proportions of a whole
  - Scatter plots: Ideal for showing relationships between variables
- Use aggregations to simplify complex datasets
- Apply filters to focus on specific subsets of data
- For time series data, use time-based aggregations to identify trends

## Technical Architecture

### Backend Components
- **Django**: Web framework for handling HTTP requests and responses
- **Django REST Framework**: API framework for building RESTful endpoints
- **Celery**: Distributed task queue for background processing
- **Redis**: Message broker for Celery and caching
- **Polars**: High-performance data processing library for dataset operations
- **Minio**: S3-compatible object storage for file storage

### Frontend Components
- **Bootstrap 5**: CSS framework for responsive UI components
- **Chart.js**: JavaScript library for interactive data visualizations
- **jQuery**: JavaScript library for DOM manipulation and AJAX requests

### Data Flow
1. User uploads a file through the web interface
2. File is temporarily stored and a Celery task is created
3. Celery worker processes the file:
   - Converts to Parquet format
   - Extracts metadata
   - Stores in Minio
4. User selects visualization parameters
5. Backend retrieves data from Minio, applies aggregations, and returns results
6. Frontend renders the visualization using Chart.js

## Conclusion

The User Dashboard application provides a powerful yet user-friendly interface for data visualization and analysis. By combining modern web technologies with efficient data processing libraries, it enables users to gain insights from their datasets without requiring specialized technical knowledge.

The application is designed to be scalable and extensible, with a modular architecture that allows for easy addition of new features and capabilities. The use of containerization through Docker ensures consistent deployment across different environments.