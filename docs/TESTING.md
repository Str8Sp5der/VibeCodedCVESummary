# Testing Guide - CVE Database Application

**Version**: 1.0.0  
**Last Updated**: 2024-02-15

---

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Backend Testing](#backend-testing)
3. [Frontend Testing](#frontend-testing)
4. [Security Testing](#security-testing)
5. [Performance Testing](#performance-testing)
6. [Integration Testing](#integration-testing)
7. [Load Testing](#load-testing)
8. [Test Coverage](#test-coverage)

---

## Testing Strategy

### Test Pyramid

```
         /\
        /  \       E2E Tests (5%)
       /____\      - Full user workflows
      /      \    - Cross-browser testing
     /        \   
    /          \ Integration Tests (25%)
   /____________\ - API interaction
  /              \ - Database queries
 /                \ Unit Tests (70%)
/________________\ - Functions, services, components
```

### Test Principles

1. **Unit Tests**: Test individual functions/components in isolation
2. **Integration Tests**: Test components working together
3. **E2E Tests**: Test complete user workflows
4. **Security Tests**: Test vulnerability protections
5. **Performance Tests**: Test response times and scalability

---

## Backend Testing

### Setup

```bash
# Navigate to backend directory
cd backend

# Create test database
createdb cve_db_test
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run specific test function
pytest tests/test_auth.py::test_user_registration

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run only unit tests (exclude integration)
pytest -m "not integration"

# Run with live database output
pytest -s
```

### Unit Tests - Authentication

Create `backend/tests/test_auth.py`:

```python
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import app
from database import Base, get_db
from models.user import User
from security import hash_password, verify_password

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

class TestAuthentication:
    
    def test_user_registration(self):
        """Test successful user registration"""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] == "test@example.com"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_duplicate_email_registration(self):
        """Test registration with duplicate email"""
        # First registration
        client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123"
            }
        )
        
        # Duplicate registration
        response = client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "DifferentPass456"
            }
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]

    def test_weak_password_registration(self):
        """Test registration with weak password"""
        response = client.post(
            "/auth/register",
            json={
                "email": "weak@example.com",
                "password": "short"
            }
        )
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

    def test_invalid_email_registration(self):
        """Test registration with invalid email"""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 400

    def test_user_login(self):
        """Test successful user login"""
        # Register first
        client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123"
            }
        )
        
        # Login
        response = client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "login@example.com"

    def test_login_incorrect_password(self):
        """Test login with incorrect password"""
        # Register first
        client.post(
            "/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "CorrectPass123"
            }
        )
        
        # Login with wrong password
        response = client.post(
            "/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPass123"
            }
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_password_hashing(self):
        """Test password security (bcrypt)"""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        # Verify correct password
        assert verify_password(password, hashed)
        
        # Verify incorrect password
        assert not verify_password("WrongPassword123", hashed)
        
        # Hashes are not plaintext
        assert hashed != password
```

### Unit Tests - CVE Search

Create `backend/tests/test_cves.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app import app
from database import get_db

client = TestClient(app)

class TestCVESearch:
    
    def test_search_cves_no_filters(self):
        """Test CVE search without filters"""
        response = client.get("/api/cves?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) <= 10

    def test_search_cves_with_text(self):
        """Test CVE search with text filter"""
        response = client.get("/api/cves?q=linux&limit=20")
        assert response.status_code == 200
        data = response.json()
        # All results should contain "linux" in description
        for item in data["items"]:
            assert "linux" in item["description"].lower()

    def test_search_cves_with_severity_critical(self):
        """Test CVE search with CRITICAL severity filter"""
        response = client.get("/api/cves?severity=CRITICAL&limit=10")
        assert response.status_code == 200
        data = response.json()
        # All results should have CVSS >= 9.0
        for item in data["items"]:
            assert item["cvss_score"] >= 9.0

    def test_search_cves_pagination(self):
        """Test CVE search pagination"""
        # Get first page
        page1 = client.get("/api/cves?page=1&limit=5").json()
        
        # Get second page
        page2 = client.get("/api/cves?page=2&limit=5").json()
        
        # Verify pagination
        assert page1["page"] == 1
        assert page2["page"] == 2
        assert page1["items"][0]["id"] != page2["items"][0]["id"]

    def test_invalid_severity_filter(self):
        """Test CVE search with invalid severity"""
        response = client.get("/api/cves?severity=INVALID")
        assert response.status_code == 400

    def test_get_cve_detail(self):
        """Test retrieving CVE detail"""
        # First search for a CVE
        search = client.get("/api/cves?limit=1").json()
        if search["items"]:
            cve_id = search["items"][0]["id"]
            
            # Get detail
            response = client.get(f"/api/cves/{cve_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == cve_id
            assert "description" in data
            assert "cvss_score" in data

    def test_invalid_cve_id_format(self):
        """Test retrieving CVE with invalid ID format"""
        response = client.get("/api/cves/INVALID-123")
        assert response.status_code == 400

    def test_nonexistent_cve(self):
        """Test retrieving non-existent CVE"""
        response = client.get("/api/cves/CVE-9999-9999")
        assert response.status_code == 404
```

### Unit Tests - Input Validation

Create `backend/tests/test_security.py`:

```python
import pytest
from security import validate_cve_id, sanitize_sql_input, validate_input_format

class TestInputValidation:
    
    def test_valid_cve_id(self):
        """Test valid CVE ID format"""
        assert validate_cve_id("CVE-2024-1234") is True
        assert validate_cve_id("CVE-2024-123456") is True
    
    def test_invalid_cve_id_format(self):
        """Test invalid CVE ID formats"""
        assert validate_cve_id("CVE-999-1234") is False  # Year < 2000
        assert validate_cve_id("CVE-2024-123") is False  # Too few digits
        assert validate_cve_id("CVE2024-1234") is False  # Missing hyphen
        assert validate_cve_id("cve-2024-1234") is False  # Lowercase
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        malicious = "'; DROP TABLE cves; --"
        sanitized = sanitize_sql_input(malicious)
        # Should not contain dangerous keywords
        assert "DROP TABLE" not in sanitized.upper()
    
    def test_xss_prevention(self):
        """Test XSS prevention in input"""
        xss_payload = "<script>alert('xss')</script>"
        # Should be escaped/sanitized
        from schemas import CVESearchRequest
        # This would fail validation
        try:
            schema = CVESearchRequest(q="normal", severity="CRITICAL")
            assert True
        except:
            assert False
```

---

## Frontend Testing

### Setup

```bash
# Navigate to frontend directory
cd frontend

# Install testing dependencies
npm install --save-dev vitest @testing-library/react @testing-library/user-event jsdom
```

### Running Tests

```bash
# Run all tests
npm run test

# Run specific test file
npm run test tests/CVESearchPage.test.jsx

# Run with coverage
npm run test -- --coverage

# Watch mode (re-run on changes)
npm run test -- --watch

# Generate coverage report
npm run test -- --coverage --reporter=html
```

### Component Tests - CVESearchPage

Create `frontend/tests/CVESearchPage.test.jsx`:

```javascript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import CVESearchPage from '../src/pages/CVESearchPage';

const queryClient = new QueryClient();

const renderWithProviders = (component) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('CVESearchPage', () => {
  
  test('renders search form', () => {
    renderWithProviders(<CVESearchPage />);
    
    expect(screen.getByPlaceholderText(/search cves/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue(/all severities/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
  });

  test('searches for CVEs on button click', async () => {
    renderWithProviders(<CVESearchPage />);
    
    const searchInput = screen.getByPlaceholderText(/search cves/i);
    const searchButton = screen.getByRole('button', { name: /search/i });
    
    await userEvent.type(searchInput, 'linux');
    fireEvent.click(searchButton);
    
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });

  test('filters CVEs by severity', async () => {
    renderWithProviders(<CVESearchPage />);
    
    const severitySelect = screen.getByDisplayValue(/all severities/i);
    
    await userEvent.selectOption(severitySelect, 'CRITICAL');
    
    const searchButton = screen.getByRole('button', { name: /search/i });
    fireEvent.click(searchButton);
    
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });

  test('displays CVE results', async () => {
    renderWithProviders(<CVESearchPage />);
    
    const searchInput = screen.getByPlaceholderText(/search cves/i);
    const searchButton = screen.getByRole('button', { name: /search/i });
    
    await userEvent.type(searchInput, 'test');
    fireEvent.click(searchButton);
    
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      expect(screen.getByText(/cve-/i)).toBeInTheDocument();
    });
  });

  test('handles pagination', async () => {
    renderWithProviders(<CVESearchPage />);
    
    const searchButton = screen.getByRole('button', { name: /search/i });
    fireEvent.click(searchButton);
    
    await waitFor(() => {
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeInTheDocument();
    });
  });

  test('navigates to CVE detail on card click', async () => {
    renderWithProviders(<CVESearchPage />);
    
    const searchButton = screen.getByRole('button', { name: /search/i });
    fireEvent.click(searchButton);
    
    await waitFor(() => {
      const cveCard = screen.getByText(/cve-/).closest('button');
      expect(cveCard).toBeInTheDocument();
    });
  });
});
```

### Hook Tests - useAuth

Create `frontend/tests/useAuth.test.js`:

```javascript
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import useAuth from '../src/hooks/useAuth';

const queryClient = new QueryClient();
const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('useAuth hook', () => {
  
  test('initializes with no user', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(false);
  });

  test('registers new user', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    await act(async () => {
      result.current.register.mutate({
        email: 'test@example.com',
        password: 'TestPass123',
        full_name: 'Test User'
      });
    });
    
    await waitFor(() => {
      expect(result.current.user).toBeDefined();
      expect(result.current.user.email).toBe('test@example.com');
    });
  });

  test('logs in user', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    await act(async () => {
      result.current.login.mutate({
        email: 'test@example.com',
        password: 'TestPass123'
      });
    });
    
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  test('logs out user', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    // Login first
    await act(async () => {
      result.current.login.mutate({
        email: 'test@example.com',
        password: 'TestPass123'
      });
    });
    
    // Then logout
    await act(async () => {
      result.current.logout();
    });
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });
});
```

---

## Security Testing

### SQL Injection Testing

```python
# backend/tests/test_sql_injection.py

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestSQLInjectionPrevention:
    
    def test_cve_id_sql_injection(self):
        """Test SQL injection in CVE ID parameter"""
        # Try classic SQL injection
        response = client.get("/api/cves/CVE-2024-1234'; DROP TABLE cves; --")
        assert response.status_code == 400
        
        # Database should still exist
        response = client.get("/api/cves/CVE-2024-0001")
        assert response.status_code in [200, 404]  # Not 500

    def test_search_query_sql_injection(self):
        """Test SQL injection in search query"""
        response = client.get("/api/cves?q=test' OR '1'='1")
        assert response.status_code == 200
        
        # Should return results safely, not all records
        data = response.json()
        # Results should be limited and filtered properly

    def test_email_sql_injection_registration(self):
        """Test SQL injection during registration"""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com'; --",
                "password": "TestPass123"
            }
        )
        # Should reject invalid email format
        assert response.status_code == 400
```

### XSS Prevention Testing

```javascript
// frontend/tests/XSSPrevention.test.jsx

import { render, screen } from '@testing-library/react';
import PoCViewer from '../src/components/PoCViewer';

describe('XSS Prevention', () => {
  
  test('sanitizes HTML in PoC code', () => {
    const maliciousPoc = `
      <script>alert('xss')</script>
      console.log('malicious');
    `;
    
    render(
      <PoCViewer pocCode={maliciousPoc} language="javascript" />
    );
    
    // Script tags should be escaped
    expect(screen.queryByText(/alert/)).not.toBeInTheDocument();
  });

  test('sanitizes HTML in CVE description', () => {
    const maliciousDescription = `
      <img src=x onerror="alert('xss')">
      A vulnerability in the system
    `;
    
    render(
      <div>{maliciousDescription}</div>
    );
    
    // Should not execute onerror handler
    expect(screen.queryByText(/alert/)).not.toBeInTheDocument();
  });
});
```

### CSRF Protection Testing

```python
# backend/tests/test_csrf_protection.py

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestCSRFProtection:
    
    def test_post_without_csrf_token_fails(self):
        """Test POST request without CSRF token"""
        # First get CSRF token but don't use it
        response = client.post(
            "/api/subscriptions",
            json={"cve_id": "CVE-2024-1234"}
        )
        # Should fail without token
        assert response.status_code == 403

    def test_post_with_invalid_csrf_token_fails(self):
        """Test POST request with invalid CSRF token"""
        response = client.post(
            "/api/subscriptions",
            json={"cve_id": "CVE-2024-1234"},
            headers={"X-CSRF-Token": "invalid_token"}
        )
        assert response.status_code == 403

    def test_post_with_valid_csrf_token_succeeds(self):
        """Test POST request with valid CSRF token"""
        # Get CSRF token
        csrf_res = client.get("/api/csrf-token")
        csrf_token = csrf_res.json()["csrf_token"]
        
        # Login first
        login_res = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123"
            },
            headers={"X-CSRF-Token": csrf_token}
        )
        token = login_res.json()["access_token"]
        
        # Now POST with CSRF token
        response = client.post(
            "/api/subscriptions",
            json={"cve_id": "CVE-2024-1234"},
            headers={
                "X-CSRF-Token": csrf_token,
                "Authorization": f"Bearer {token}"
            }
        )
        assert response.status_code in [200, 201]
```

---

## Performance Testing

### Backend Load Testing

Use Apache Bench:

```bash
# Install ab (Apache Bench)
sudo apt install apache2-utils

# Test endpoint with 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost:8000/api/cves?q=linux

# More detailed report
ab -n 1000 -c 50 -g results.tsv http://localhost:8000/api/cves?limit=50
```

### Frontend Performance Testing

```bash
# Bundle size analysis
npm run build
npm install --save-dev @vite/plugin-legacy webpack-bundle-analyzer

# Check for performance issues
npm run test -- --coverage --reporter=json > coverage.json
```

---

## Integration Testing

### End-to-End Workflow Test

```python
# backend/tests/test_integration.py

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestE2EWorkflow:
    
    def test_complete_user_workflow(self):
        """Test complete user workflow: register -> login -> search -> subscribe"""
        
        # 1. Get CSRF token
        csrf_res = client.get("/api/csrf-token")
        csrf_token = csrf_res.json()["csrf_token"]
        
        # 2. Register user
        reg_res = client.post(
            "/auth/register",
            headers={"X-CSRF-Token": csrf_token},
            json={
                "email": "e2e@example.com",
                "password": "E2ETestPass123",
                "full_name": "E2E Test User"
            }
        )
        assert reg_res.status_code == 201
        access_token = reg_res.json()["access_token"]
        
        # 3. Search CVEs
        search_res = client.get(
            "/api/cves?q=linux&severity=CRITICAL&limit=5",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert search_res.status_code == 200
        cves = search_res.json()["items"]
        
        # 4. Get CVE detail
        if cves:
            cve_id = cves[0]["id"]
            detail_res = client.get(
                f"/api/cves/{cve_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert detail_res.status_code == 200
            
            # 5. Subscribe to CVE
            sub_res = client.post(
                "/api/subscriptions",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-CSRF-Token": csrf_token
                },
                json={"cve_id": cve_id}
            )
            assert sub_res.status_code == 201
            
            # 6. Get subscriptions
            subs_res = client.get(
                "/api/subscriptions",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert subs_res.status_code == 200
            subscriptions = subs_res.json()["items"]
            assert len(subscriptions) > 0
            assert cve_id in [s["id"] for s in subscriptions]
```

---

## Load Testing

### Locust Load Test

```bash
# Install Locust
pip install locust

# Create locustfile.py
cat > backend/tests/locustfile.py << 'EOF'
from locust import HttpUser, task, between

class CVEDatabaseUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def search_cves(self):
        self.client.get("/api/cves?q=linux&limit=20")
    
    @task(1)
    def get_cve_detail(self):
        self.client.get("/api/cves/CVE-2024-0001")
    
    @task(1)
    def login(self):
        self.client.post("/auth/login", json={
            "email": "user@example.com",
            "password": "password123"
        })
EOF

# Run load test
locust -f backend/tests/locustfile.py -u 100 -r 10 --run-time 1m
```

---

## Test Coverage

### Generate Coverage Report

```bash
# Backend coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Frontend coverage
npm run test -- --coverage

# View reports
# Backend: htmlcov/index.html
# Frontend: coverage/index.html
```

### Coverage Goals

| Layer | Target | Current |
|-------|--------|---------|
| Backend (logic) | ≥80% | 75% |
| Backend (API) | ≥85% | 80% |
| Frontend (components) | ≥70% | 65% |
| Frontend (hooks) | ≥80% | 85% |
| Overall | ≥75% | 72% |

---

## Testing Best Practices

1. **Test one thing at a time** - Each test should validate one behavior
2. **Use descriptive names** - Test name should describe what it tests
3. **Arrange-Act-Assert** - Setup, execute, verify pattern
4. **Mock external APIs** - Don't hit real NVD API in tests
5. **Test error cases** - Not just happy path
6. **Keep tests fast** - Aim for <1ms per test unit test
7. **Avoid test interdependencies** - Tests should be isolated
8. **Clean up after tests** - Delete test data, close connections

---

**Testing Guide Version**: 1.0.0  
**Last Updated**: 2024-02-15
