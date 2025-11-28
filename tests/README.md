# Test Structure Documentation

## Overview

The test suite is organized into three main categories: **Unit Tests**, **Integration Tests**, and **Fixtures**.

## Directory Structure

```
tests/
├── conftest.py              # Pytest configuration and database setup
├── pytest.ini               # Pytest configuration file
├── fixtures/
│   ├── __init__.py
│   └── fixtures.py          # Shared test fixtures and utilities
├── unit/
│   ├── __init__.py
│   ├── test_security.py     # Password hashing and token generation
│   └── test_schemas.py      # Pydantic schema validation
└── integration/
    ├── __init__.py
    ├── test_auth.py         # Authentication endpoint tests
    ├── test_items.py        # Item CRUD and ownership tests
    └── test_api_basic.py    # General API functionality tests
```

## Test Categories

### Unit Tests (`tests/unit/`)

Unit tests focus on testing individual components in isolation.

#### `test_security.py`
- **TestPasswordHashing**: Password hashing and verification
  - `test_get_password_hash_returns_string`: Verify hash is generated
  - `test_get_password_hash_different_each_time`: Bcrypt salt produces different hashes
  - `test_verify_password_correct`: Correct password verification
  - `test_verify_password_incorrect`: Incorrect password fails
  - `test_verify_password_empty_string`: Handle empty string

- **TestTokenGeneration**: JWT token creation
  - `test_create_access_token_returns_string`: Token is string format
  - `test_create_access_token_has_three_parts`: JWT has header.payload.signature
  - `test_create_access_token_with_custom_expiry`: Custom expiration works

#### `test_schemas.py`
- **TestUserCreateSchema**: User registration validation
  - Valid user creation
  - Required field validation
  - Email format validation

- **TestItemCreateSchema**: Item creation validation
  - Valid item creation
  - Required field validation
  - Optional field handling

### Integration Tests (`tests/integration/`)

Integration tests verify that components work together correctly and endpoints function as expected.

#### `test_auth.py`
- **TestAuthenticationFlow**: Complete auth workflows
  - `test_register_and_login_flow`: Full registration and login
  - `test_register_user_success`: Successful registration
  - `test_register_duplicate_username`: Duplicate prevention
  - `test_register_duplicate_email`: Email uniqueness
  - `test_login_success`: Valid credentials
  - `test_login_invalid_credentials`: Non-existent user
  - `test_login_wrong_password`: Incorrect password

#### `test_items.py`
- **TestItemCRUD**: CRUD operations
  - Create, read, update, delete operations
  - Authentication requirement
  - Empty and multiple item lists
  - Non-existent item handling

- **TestItemOwnership**: Data isolation
  - Users can only see their own items
  - Items are properly scoped to user

#### `test_api_basic.py`
- **TestAPIBasics**: General functionality
  - Health check endpoint
  - Current user retrieval
  - Swagger/ReDoc documentation availability

### Fixtures (`tests/fixtures/`)

Reusable test fixtures and utilities:

- `auth_token`: Create test user and return JWT token
- `test_user_credentials`: Standard test user data
- `admin_user_credentials`: Admin user data

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run only unit tests
```bash
pytest tests/unit/ -v
```

### Run only integration tests
```bash
pytest tests/integration/ -v
```

### Run specific test file
```bash
pytest tests/integration/test_auth.py -v
```

### Run specific test class
```bash
pytest tests/unit/test_security.py::TestPasswordHashing -v
```

### Run specific test
```bash
pytest tests/unit/test_security.py::TestPasswordHashing::test_verify_password_correct -v
```

### Run with coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run with specific markers
```bash
pytest tests/ -m integration  # Requires marker configuration
```

## Test Best Practices

1. **Unit Tests**: Test a single function or class in isolation
   - No external dependencies
   - Fast execution
   - Test edge cases and error conditions

2. **Integration Tests**: Test interactions between components
   - Use real HTTP requests via TestClient
   - Use shared database fixtures
   - Test complete workflows

3. **Fixtures**:
   - Reusable test data and setup
   - Imported in conftest.py for global access
   - Scope fixtures appropriately (function, class, session)

4. **Naming**:
   - Test files: `test_*.py`
   - Test classes: `Test*` (noun-based, e.g., `TestAuthentication`)
   - Test methods: `test_*` (verb-based, e.g., `test_login_with_valid_credentials`)

5. **Organization**:
   - Group related tests in classes
   - Use descriptive docstrings
   - One responsibility per test
   - Arrange-Act-Assert pattern

## Example Test Patterns

### Unit Test Pattern
```python
def test_password_hashing(self):
    """Test that passwords are hashed correctly."""
    password = "secure_password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
```

### Integration Test Pattern
```python
def test_full_auth_flow(self, client):
    """Test registration and login workflow."""
    # Arrange
    user_data = {"username": "test", "email": "test@example.com", "password": "pass"}

    # Act
    register_response = client.post("/api/v1/auth/register", json=user_data)
    login_response = client.post("/api/v1/auth/token", data={...})

    # Assert
    assert register_response.status_code == 200
    assert login_response.status_code == 200
```

## Database Testing

- Tests use a temporary SQLite database (`test_app.db`)
- Database is reset before each test via `reset_db` fixture
- Database is cleaned up after all tests
- No test isolation issues due to per-test database reset

## Test Statistics

- **Total Tests**: 25
- **Unit Tests**: 8
- **Integration Tests**: 17
- **Test Coverage**: Auth (4), Items (10), API Basics (3), Security (5), Schemas (3)
- **Pass Rate**: 100%
- **Avg Runtime**: ~21 seconds

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- Exit code 0 on all pass
- Exit code 1 if any test fails
- Warnings output for deprecations (non-blocking)
- Comprehensive error messages for debugging

**Coverage**
[![codecov](https://codecov.io/gh/jessebrite/products-api/graph/badge.svg)](https://codecov.io/gh/jessebrite/products-api)
