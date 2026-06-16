# Test Suite for repo-intel

This directory contains the test suite for the repo-intel project.

## Test Structure

### Unit Tests
- **`test_cli.py`** - Tests for CLI argument parsing and command execution
- **`test_engine.py`** - Tests for the core ContextEngine and data models
- **`test_modules.py`** - Tests for signal modules and their integration

### Integration Tests
- **`test_integration.py`** - End-to-end tests and real-world scenarios

## Running Tests

### Quick Test Run
```bash
uv run pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
uv run pytest tests/ -m "not integration"

# Integration tests only
uv run pytest tests/ -m integration

# Specific test file
uv run pytest tests/test_engine.py -v
```

### With Coverage
```bash
uv run pytest --cov=repo_intel --cov-report=html tests/
```

### Using the Test Runner Script
```bash
# Run all tests
python tests/run_tests.py

# Run with coverage
python tests/run_tests.py --coverage

# Run with linting
python tests/run_tests.py --lint
```

## Test Categories

- **`unit`** - Fast tests that don't require external dependencies
- **`integration`** - Tests that may require network access or external tools
- **`slow`** - Tests that take longer to run

## Writing New Tests

1. Unit tests should be fast and not depend on external services
2. Use mocks for external dependencies (GitHub API, network calls)
3. Integration tests can use real repositories but should be careful with API limits
4. Follow the existing naming conventions:
   - Test classes: `TestClassName`
   - Test methods: `test_specific_behavior`

## Test Data

The tests use the `code_intel_test_repo` directory for integration testing when available. This repository contains sample code with various security patterns for testing.

## Configuration

Test configuration is in `pytest.ini` and `conftest.py`:
- Fixtures for common test data
- Test markers and filtering
- Output formatting
