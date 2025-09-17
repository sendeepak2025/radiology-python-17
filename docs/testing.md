# Kiro-mini Testing Guide

This guide covers testing strategies, test execution, and test development for Kiro-mini.

## Testing Overview

Kiro-mini uses a comprehensive testing strategy that includes:

- **Unit Tests**: Test individual components and services
- **Integration Tests**: Test complete workflows and component interactions
- **API Tests**: Test REST API endpoints and responses
- **Performance Tests**: Validate performance targets and benchmarks
- **End-to-End Tests**: Test complete user workflows

## Test Structure

```
backend/tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_services.py         # Unit tests for services
├── test_api.py             # API endpoint tests
├── test_integration.py     # Integration workflow tests
├── test_performance.py     # Performance and load tests
├── run_tests.py           # Test runner script
└── pytest.ini            # Pytest configuration
```

## Running Tests

### Quick Start

```bash
# Navigate to backend directory
cd backend

# Run all tests
python tests/run_tests.py

# Run with coverage
python tests/run_tests.py --coverage
```

### Test Categories

```bash
# Unit tests only
python tests/run_tests.py --unit

# Integration tests
python tests/run_tests.py --integration

# API tests
python tests/run_tests.py --api

# Performance tests
python tests/run_tests.py --performance

# Service tests
python tests/run_tests.py --services
```

### Advanced Options

```bash
# Verbose output
python tests/run_tests.py --verbose

# Parallel execution
python tests/run_tests.py --parallel 4

# Skip slow tests
python tests/run_tests.py --fast

# Run specific test file
pytest tests/test_services.py -v

# Run specific test class
pytest tests/test_services.py::TestAuditService -v

# Run specific test method
pytest tests/test_services.py::TestAuditService::test_log_event -v
```

## Test Environment Setup

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Set up test database
createdb kiro_mini_test

# Set test environment variables
export DATABASE_URL=postgresql://user:password@localhost/kiro_mini_test
export REDIS_URL=redis://localhost:6379/1
export TESTING=true
```

### Docker Test Environment

```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Run tests in container
docker-compose -f docker-compose.test.yml exec backend python tests/run_tests.py
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --disable-warnings
    --tb=short
    --maxfail=10
    --durations=10
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    unit: marks tests as unit tests
    api: marks tests as API tests
    services: marks tests as service tests
    asyncio: marks tests as async tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
asyncio_mode = auto
```

### Test Fixtures (`conftest.py`)

Key fixtures available for tests:

- `test_db`: Test database session
- `client`: FastAPI test client
- `sample_study`: Sample study for testing
- `sample_report`: Sample report for testing
- `sample_superbill`: Sample superbill for testing
- `audit_service`: Audit service instance
- `fhir_service`: FHIR service instance
- `x12_service`: X12 service instance
- `webhook_service`: Webhook service instance

## Writing Tests

### Unit Test Example

```python
import pytest
from services.audit_service import AuditService

class TestAuditService:
    """Test cases for AuditService."""
    
    @pytest.mark.asyncio
    async def test_log_event(self, test_db, audit_service):
        """Test logging an audit event."""
        # Arrange
        event_data = {
            "event_type": "TEST_EVENT",
            "event_description": "Test event description",
            "resource_type": "Test",
            "resource_id": "test_123",
            "user_id": "test_user"
        }
        
        # Act
        await audit_service.log_event(db=test_db, **event_data)
        
        # Assert
        audit_log = test_db.query(AuditLog).filter(
            AuditLog.event_type == "TEST_EVENT"
        ).first()
        
        assert audit_log is not None
        assert audit_log.event_description == "Test event description"
        assert audit_log.user_id == "test_user"
```

### API Test Example

```python
def test_create_report(self, client, sample_study):
    """Test creating a new report."""
    # Arrange
    report_data = {
        "study_uid": sample_study.study_uid,
        "radiologist_id": "test_radiologist",
        "exam_type": sample_study.exam_type,
        "findings": "Test findings",
        "impressions": "Test impressions",
        "recommendations": "Test recommendations",
        "diagnosis_codes": ["Z01.818"],
        "cpt_codes": ["93306"]
    }
    
    # Act
    response = client.post("/reports", json=report_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["study_uid"] == sample_study.study_uid
    assert data["findings"] == "Test findings"
    assert data["status"] == "draft"
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_complete_workflow(self, test_db, client):
    """Test complete study-to-billing workflow."""
    # Step 1: Ingest study
    study_data = {
        "patient_id": "WORKFLOW001",
        "study_date": "2024-01-15",
        "modality": "US",
        "exam_type": "echo_complete",
        "study_description": "Complete Echocardiogram"
    }
    
    study_uid = "1.2.3.4.5.6.7.8.9.workflow"
    response = client.post(f"/studies/{study_uid}/ingest", json=study_data)
    assert response.status_code == 200
    
    # Step 2: Create report
    report_data = {
        "study_uid": study_uid,
        "radiologist_id": "workflow_radiologist",
        "exam_type": "echo_complete",
        "findings": "Normal cardiac function",
        "impressions": "Normal echocardiogram",
        "recommendations": "No follow-up required",
        "diagnosis_codes": ["Z01.818"],
        "cpt_codes": ["93306"]
    }
    
    response = client.post("/reports", json=report_data)
    assert response.status_code == 200
    report_id = response.json()["report_id"]
    
    # Step 3: Finalize report
    response = client.post(f"/reports/{report_id}/finalize")
    assert response.status_code == 200
    
    # Step 4: Generate superbill
    response = client.post("/superbills", json={"report_id": report_id})
    assert response.status_code == 200
    
    # Verify complete workflow
    superbill_data = response.json()
    assert superbill_data["total_charges"] > 0
    assert len(superbill_data["services"]) > 0
```

### Performance Test Example

```python
def test_study_ingestion_performance(self, client):
    """Test study ingestion meets performance targets."""
    study_data = {
        "patient_id": "PERF001",
        "study_date": "2024-01-15",
        "modality": "US",
        "exam_type": "echo_complete",
        "study_description": "Performance Test Echo"
    }
    
    study_uid = "1.2.3.4.5.6.7.8.9.perf"
    
    start_time = time.time()
    response = client.post(f"/studies/{study_uid}/ingest", json=study_data)
    end_time = time.time()
    
    assert response.status_code == 200
    
    # Should complete within 2 seconds
    ingestion_time = end_time - start_time
    assert ingestion_time < 2.0, f"Study ingestion took {ingestion_time:.2f}s, exceeding 2s target"
```

## Test Data Management

### Creating Test Data

```python
# In conftest.py
@pytest.fixture
def sample_study(test_db):
    """Create a sample study for testing."""
    study = Study(
        study_uid="1.2.3.4.5.6.7.8.9.test",
        patient_id="TEST001",
        study_date="2024-01-15",
        modality="US",
        exam_type="echo_complete",
        study_description="Test Echocardiogram",
        status="completed"
    )
    test_db.add(study)
    test_db.commit()
    test_db.refresh(study)
    return study
```

### Test Data Cleanup

```python
@pytest.fixture(autouse=True)
def cleanup_test_data(test_db):
    """Clean up test data after each test."""
    yield
    # Cleanup is handled by test database rollback
    test_db.rollback()
```

## Mocking External Services

### Mocking AI Service

```python
@patch('services.ai_service.AIService.generate_report')
def test_ai_report_generation(self, mock_ai, client, sample_study):
    """Test AI report generation with mocked service."""
    mock_ai.return_value = {
        "findings": "AI generated findings",
        "impressions": "AI generated impressions",
        "confidence": 0.95
    }
    
    response = client.post("/ai/assist-report", json={
        "study_uid": sample_study.study_uid,
        "exam_type": sample_study.exam_type
    })
    
    assert response.status_code == 200
    assert mock_ai.called
```

### Mocking Webhook Endpoints

```python
@pytest.fixture
def mock_webhook_server():
    """Create a mock webhook server for testing."""
    import threading
    import http.server
    import socketserver
    
    class MockWebhookHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            self.server.last_request = {
                'headers': dict(self.headers),
                'body': post_data.decode('utf-8'),
                'path': self.path
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "received"}')
    
    port = 8999
    server = socketserver.TCPServer(("", port), MockWebhookHandler)
    server.last_request = None
    
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    yield f"http://localhost:{port}", server
    
    server.shutdown()
    server.server_close()
```

## Test Markers and Categories

### Using Test Markers

```python
@pytest.mark.slow
def test_large_dataset_processing(self):
    """Test processing large datasets (marked as slow)."""
    pass

@pytest.mark.integration
def test_end_to_end_workflow(self):
    """Test complete end-to-end workflow."""
    pass

@pytest.mark.performance
def test_concurrent_requests(self):
    """Test performance under concurrent load."""
    pass
```

### Running Specific Markers

```bash
# Run only fast tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run performance tests
pytest -m performance

# Combine markers
pytest -m "integration and not slow"
```

## Coverage Reporting

### Generate Coverage Report

```bash
# Run tests with coverage
python tests/run_tests.py --coverage

# Generate HTML report
pytest --cov=. --cov-report=html

# Generate XML report (for CI)
pytest --cov=. --cov-report=xml

# View coverage in terminal
pytest --cov=. --cov-report=term-missing
```

### Coverage Configuration

Create `.coveragerc`:

```ini
[run]
source = .
omit = 
    */tests/*
    */venv/*
    */migrations/*
    */scripts/*
    setup.py
    conftest.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

[html]
directory = htmlcov
```

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: kiro_mini_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/kiro_mini_test
        REDIS_URL: redis://localhost:6379/1
        TESTING: true
      run: |
        cd backend
        python tests/run_tests.py --coverage
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        fail_ci_if_error: true
```

## Test Performance Optimization

### Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto

# Specify number of workers
pytest -n 4
```

### Database Test Optimization

```python
# Use transaction rollback for faster cleanup
@pytest.fixture
def test_db():
    """Create a test database session with transaction rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

### Async Test Optimization

```python
# Use pytest-asyncio for async tests
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await some_async_function()
    assert result is not None
```

## Test Debugging

### Debug Test Failures

```bash
# Run with pdb on failure
pytest --pdb

# Run with verbose output
pytest -v -s

# Run specific failing test
pytest tests/test_services.py::TestAuditService::test_log_event -v -s

# Show local variables on failure
pytest --tb=long
```

### Test Logging

```python
import logging

def test_with_logging(caplog):
    """Test with log capture."""
    with caplog.at_level(logging.INFO):
        some_function_that_logs()
    
    assert "Expected log message" in caplog.text
```

## Best Practices

### Test Organization

1. **Group related tests** in classes
2. **Use descriptive test names** that explain what is being tested
3. **Follow AAA pattern** (Arrange, Act, Assert)
4. **Keep tests independent** - each test should be able to run in isolation
5. **Use fixtures** for common test data and setup

### Test Data

1. **Use minimal test data** that covers the test case
2. **Create focused fixtures** for specific test scenarios
3. **Clean up test data** after each test
4. **Use factories** for generating test data variations

### Assertions

1. **Use specific assertions** rather than generic ones
2. **Test both positive and negative cases**
3. **Include error message context** in assertions
4. **Test edge cases and boundary conditions**

### Performance Testing

1. **Set realistic performance targets** based on requirements
2. **Test under realistic load conditions**
3. **Monitor resource usage** during performance tests
4. **Use appropriate test data sizes**

This testing guide provides comprehensive coverage of testing strategies and practices for Kiro-mini, ensuring high code quality and system reliability.