# Contributing to User Dashboard

Thank you for your interest in contributing to the User Dashboard project! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect different viewpoints and experiences
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- Git
- Basic knowledge of Django and web development

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git fork https://github.com/your-username/userdashboard.git
   git clone https://github.com/your-username/userdashboard.git
   cd userdashboard
   ```

2. **Set up development environment**:
   ```bash
   # Quick setup (recommended)
   ./setup-dev.sh  # Linux/macOS
   setup-dev.bat   # Windows
   
   # Or manually
   make setup-dev
   ```

3. **Verify setup**:
   ```bash
   make check
   make test
   ```

## Making Changes

### Branch Naming Convention

Use descriptive branch names with prefixes:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

Examples:
- `feature/user-profile-management`
- `bugfix/file-upload-validation`
- `docs/api-documentation-update`

### Commit Message Guidelines

Follow the conventional commit format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(dashboard): add data export functionality

fix(upload): resolve file validation error for large files

docs(readme): update installation instructions

test(api): add unit tests for dataset endpoints
```

## Code Style Guidelines

### Python Code Style

This project uses automated code formatting and linting:

- **Line Length**: 120 characters maximum
- **Code Formatting**: Black formatter
- **Import Organization**: isort
- **Linting**: pylint, flake8
- **Type Hints**: Encouraged for new code
- **Docstrings**: Google-style docstrings

### Pre-commit Hooks

Pre-commit hooks automatically run on every commit:

```bash
# Install hooks (done automatically by setup scripts)
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Code Quality Commands

```bash
# Format code
make format

# Run all linting
make lint

# Run all checks
make check

# Run tests
make test
```

## Testing

### Writing Tests

- Write tests for all new functionality
- Use pytest for testing
- Follow the existing test structure
- Include both unit and integration tests
- Test edge cases and error conditions

### Test Structure

```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_views.py
│   └── test_utils.py
├── integration/
│   ├── test_api.py
│   └── test_workflows.py
└── fixtures/
    └── sample_data.py
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
python manage.py test tests.unit.test_models

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## Submitting Changes

### Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**:
   ```bash
   make check
   make test
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Use a descriptive title
   - Include a detailed description
   - Reference any related issues
   - Add screenshots for UI changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

## Review Process

### What We Look For

- **Code Quality**: Clean, readable, and maintainable code
- **Testing**: Adequate test coverage for new functionality
- **Documentation**: Updated documentation for new features
- **Performance**: No significant performance regressions
- **Security**: No security vulnerabilities introduced
- **Compatibility**: Backward compatibility maintained

### Review Timeline

- Initial review within 2-3 business days
- Follow-up reviews within 1-2 business days
- Merge after approval and CI checks pass

### Addressing Feedback

- Respond to all review comments
- Make requested changes promptly
- Ask for clarification if feedback is unclear
- Update tests and documentation as needed

## Development Guidelines

### Database Changes

- Create migrations for model changes
- Test migrations on sample data
- Consider backward compatibility
- Document breaking changes

### API Changes

- Maintain backward compatibility
- Update API documentation
- Add appropriate tests
- Consider versioning for breaking changes

### Security Considerations

- Validate all user inputs
- Use Django's built-in security features
- Follow OWASP guidelines
- Run security scans before submitting

### Performance Guidelines

- Profile code for performance bottlenecks
- Optimize database queries
- Consider caching for expensive operations
- Test with large datasets

## Getting Help

- **Documentation**: Check the README and project documentation
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Ask for help during the review process

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for significant contributions
- README.md contributors section
- Release notes for major features

Thank you for contributing to the User Dashboard project!
