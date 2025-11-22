# Testing Guide & Best Practices

## Quick Start

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/test_security.py -v

# Run specific test class
pytest tests/unit/test_security.py::TestPasswordHashing -v

# Run specific test
pytest tests/unit/test_security.py::TestPasswordHashing::test_verify_password_correct -v
```

## Test Structure Philosophy

### Unit Tests
**Location**: `tests/unit/`
**Purpose**: Test individual functions/classes in isolation
**Characteristics**:
- No external dependencies
- No database access
- Fast execution
- Test edge cases and error conditions

```python
def test_verify_password_correct(self):
    """Test that verify_password works with correct password."""
    password = "secure_password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
```

### Integration Tests
**Location**: `tests/integration/`
**Purpose**: Test complete workflows and endpoint interactions
**Characteristics**:
- Use TestClient for HTTP requests
- Access test database
- Test real user scenarios
- Verify business logic flows

```python
def test_register_and_login_flow(self, client):
    """Test complete registration and login workflow."""
    # Register
    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": "test", "email": "test@example.com", "password": "pass"}
    )
    assert register_response.status_code == 200
    
    # Login
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "test", "password": "pass"}
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
```

## Creating New Tests

### Step 1: Decide Test Type

| Question | Answer | Type |
|----------|--------|------|
| Does it test a single function? | Yes | Unit |
| Does it test an HTTP endpoint? | Yes | Integration |
| Does it require a database? | Yes | Integration |
| Does it need other components? | Yes | Integration |

### Step 2: Create Test File

#### Unit Test Template
```python
"""Unit tests for <module>."""

import pytest
from src.module import function_to_test


class TestFunctionality:
    """Test <specific functionality>."""
    
    def test_happy_path(self):
        """Test the expected successful scenario."""
        result = function_to_test(input_data)
        assert result == expected_output
    
    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
    
    def test_edge_case(self):
        """Test edge cases."""
        result = function_to_test(edge_case_input)
        assert result == edge_case_output
```

#### Integration Test Template
```python
"""Integration tests for <feature>."""

import pytest


class TestFeatureWorkflow:
    """Test <feature> workflows."""
    
    def test_happy_path(self, client, auth_token):
        """Test the expected successful scenario."""
        response = client.post(
            "/api/v1/endpoint",
            json={"data": "value"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["expected_field"] == expected_value
    
    def test_error_case(self, client):
        """Test error handling."""
        response = client.post(
            "/api/v1/endpoint",
            json={"invalid": "data"}
        )
        assert response.status_code == 400
    
    def test_unauthorized(self, client):
        """Test authentication requirement."""
        response = client.post(
            "/api/v1/protected-endpoint",
            json={"data": "value"}
        )
        assert response.status_code == 401
```

### Step 3: Use Fixtures

#### Available Fixtures

| Fixture | Type | Purpose |
|---------|------|---------|
| `client` | Integration | FastAPI TestClient |
| `auth_token` | Integration | JWT token for authenticated requests |
| `test_user_credentials` | Unit/Integration | User login data |
| `admin_user_credentials` | Integration | Admin credentials |
| `reset_db` | Session | Database reset |

#### Fixture Usage
```python
def test_with_auth(self, client, auth_token):
    """Test authenticated endpoint."""
    response = client.get(
        "/api/v1/protected",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
```

### Step 4: Follow Conventions

#### Naming Conventions
```
test_<component>_<scenario>_<expected_result>
test_login_with_valid_credentials_returns_token
test_create_item_without_auth_returns_401
test_delete_item_successful_removes_item
```

#### Test Class Naming
```
Test<Feature>
TestAuthentication
TestItemCRUD
TestItemOwnership
```

#### File Naming
```
tests/unit/test_<module>.py
tests/integration/test_<feature>.py
tests/unit/test_security.py
tests/integration/test_auth.py
```

## Common Test Patterns

### Pattern 1: Basic Validation
```python
def test_valid_input(self):
    """Test function with valid input."""
    result = function(valid_input)
    assert result is not None
    assert result.id > 0
```

### Pattern 2: Error Handling
```python
def test_invalid_input_raises_error(self):
    """Test that function raises error for invalid input."""
    with pytest.raises(ValueError, match="specific error message"):
        function(invalid_input)
```

### Pattern 3: HTTP Request/Response
```python
def test_endpoint_success(self, client):
    """Test endpoint returns correct response."""
    response = client.post(
        "/api/v1/endpoint",
        json={"field": "value"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["field"] == "value"
```

### Pattern 4: Authentication
```python
def test_protected_endpoint_without_auth(self, client):
    """Test that protected endpoint requires auth."""
    response = client.get("/api/v1/protected")
    assert response.status_code == 401

def test_protected_endpoint_with_auth(self, client, auth_token):
    """Test that protected endpoint works with auth."""
    response = client.get(
        "/api/v1/protected",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
```

### Pattern 5: CRUD Operations
```python
def test_create_read_update_delete(self, client, auth_token):
    """Test complete CRUD workflow."""
    # Create
    create_resp = client.post(
        "/api/v1/items",
        json={"title": "Test"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert create_resp.status_code == 200
    item_id = create_resp.json()["id"]
    
    # Read
    read_resp = client.get(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert read_resp.status_code == 200
    
    # Update
    update_resp = client.put(
        f"/api/v1/items/{item_id}",
        json={"title": "Updated"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert update_resp.status_code == 200
    
    # Delete
    delete_resp = client.delete(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert delete_resp.status_code == 204
```

## Tips & Tricks

### 1. Debugging Tests
```bash
# Run with output
pytest tests/ -v -s

# Run with detailed traceback
pytest tests/ -vv --tb=long

# Stop at first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l
```

### 2. Test Markers (Future Enhancement)
```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    pass

@pytest.mark.auth
def test_authentication():
    pass

@pytest.mark.crud
def test_item_creation():
    pass
```

Run markers: `pytest -m auth`

### 3. Parametrized Tests
```python
import pytest

@pytest.mark.parametrize("username,expected", [
    ("validuser", True),
    ("", False),
    ("a" * 1000, False),  # Too long
])
def test_username_validation(self, username, expected):
    result = is_valid_username(username)
    assert result == expected
```

### 4. Fixtures with Setup/Teardown
```python
@pytest.fixture
def sample_user(client):
    """Create a test user and clean up after."""
    # Setup
    response = client.post("/api/v1/auth/register", json={...})
    user_id = response.json()["id"]
    
    yield user_id  # Test runs here
    
    # Teardown
    # Cleanup code (optional, auto-cleanup via reset_db)
```

## Troubleshooting

### Common Issues

#### Issue: "No such table: users"
**Cause**: Database not initialized for test
**Solution**: Ensure `reset_db` fixture is used

#### Issue: "Could not validate credentials"
**Cause**: Using wrong token or missing Authorization header
**Solution**: Use `auth_token` fixture and proper header format

#### Issue: Test passes locally but fails in CI
**Cause**: Timing, environment, or database issues
**Solution**: Add explicit waits, check environment variables

#### Issue: Tests are slow
**Cause**: Integration tests making real requests
**Solution**: Use mocking for external services, keep unit tests fast

## Performance Optimization

### Current Performance
- Unit Tests: ~6 seconds (16 tests)
- Integration Tests: ~16 seconds (38 tests)
- Total: ~42 seconds (63 tests)

### Optimization Tips
1. Run tests in parallel: `pytest -n auto`
2. Run only changed tests: `pytest --lf` (last failed)
3. Cache fixtures appropriately
4. Mock slow operations
5. Use focused test suites during development

## Continuous Integration

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --tb=short
```

### Expected Output
```
63 passed in 42.73s
Exit code: 0
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [TestClient](https://starlette.io/testclient/)
- [Fixture Documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html)

---

**Last Updated**: 2025-11-21
**Test Suite Version**: 2.0 (Reorganized)
**Total Tests**: 63 ✅
