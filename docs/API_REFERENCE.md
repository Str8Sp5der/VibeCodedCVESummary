# API Reference - CVE Database Application

**Version**: 1.0.0  
**Base URL**: `http://localhost:8000/` (development) or `https://api.cve-app.example.com/` (production)  
**Content-Type**: `application/json`  
**Authentication**: JWT Bearer Token (via `Authorization` header or `access_token_cookie`)

---

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [CVE Endpoints](#cve-endpoints)
3. [Subscription Endpoints](#subscription-endpoints)
4. [Admin Endpoints](#admin-endpoints)
5. [Error Responses](#error-responses)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

---

## Authentication Endpoints

### 1. Get CSRF Token

**Endpoint**: `GET /api/csrf-token`

**Description**: Retrieve a CSRF token for protecting state-changing requests (POST, PUT, DELETE).

**Request**: 
```bash
curl -X GET http://localhost:8000/api/csrf-token
```

**Response** (200 OK):
```json
{
  "csrf_token": "abcd1234efgh5678ijkl9012mnop3456==",
  "token_type": "bearer"
}
```

**Used By**: Frontend on app initialization. Store in localStorage or state.

---

### 2. Register User

**Endpoint**: `POST /auth/register`

**Description**: Create a new user account.

**Request Headers**:
```
Content-Type: application/json
X-CSRF-Token: <csrf_token_from_/api/csrf-token>
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe"
}
```

**Validation Rules**:
- `email`: Must be valid RFC 5322 email format
- `password`: Minimum 8 characters
- `full_name`: Optional, max 100 characters

**Response** (201 Created):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "viewer",
    "is_active": true,
    "created_at": "2024-02-15T10:30:00Z"
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "detail": "Email already registered"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123",
    "full_name": "John Doe"
  }'
```

---

### 3. Login User

**Endpoint**: `POST /auth/login`

**Description**: Authenticate user and receive JWT tokens.

**Request Headers**:
```
Content-Type: application/json
X-CSRF-Token: <csrf_token>
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "viewer",
    "is_active": true,
    "last_login": "2024-02-15T10:35:00Z"
  }
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Invalid email or password"
}
```

**Note**: Tokens are also set as HttpOnly cookies for XSS protection.

**cURL Example**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }' \
  -c cookies.txt  # Save cookies for subsequent requests
```

---

### 4. Refresh Access Token

**Endpoint**: `POST /auth/refresh`

**Description**: Get a new access token using a refresh token (valid for 7 days).

**Request Headers**:
```
Content-Type: application/json
Authorization: Bearer <refresh_token>
```

**Request Body**: Empty

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Invalid or expired refresh token"
}
```

---

### 5. Logout User

**Endpoint**: `POST /auth/logout`

**Description**: Invalidate tokens and logout user.

**Request Headers**:
```
Content-Type: application/json
Authorization: Bearer <access_token>
```

**Request Body**: Empty

**Response** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

---

### 6. Get Current User

**Endpoint**: `GET /api/users/me`

**Description**: Retrieve current authenticated user info.

**Request Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "analyst",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-02-15T10:30:00Z",
  "last_login": "2024-02-15T14:22:00Z"
}
```

---

## CVE Endpoints

### 1. Search CVEs

**Endpoint**: `GET /api/cves`

**Description**: Search and filter Common Vulnerabilities and Exposures.

**Query Parameters**:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `q` | string | No | Text search (CVE ID, description) | `Linux kernel` |
| `severity` | string | No | Filter by severity: LOW, MEDIUM, HIGH, CRITICAL | `CRITICAL` |
| `year` | integer | No | Filter by year published | `2024` |
| `page` | integer | No | Page number (default: 1) | `1` |
| `limit` | integer | No | Results per page, max 50 (default: 20) | `50` |

**Request**:
```bash
curl -X GET "http://localhost:8000/api/cves?q=linux&severity=CRITICAL&year=2024&page=1&limit=50"
```

**Response** (200 OK):
```json
{
  "total": 342,
  "page": 1,
  "limit": 50,
  "total_pages": 7,
  "items": [
    {
      "id": "CVE-2024-0001",
      "description": "Buffer overflow in Linux kernel...",
      "cvss_score": 9.8,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
      "published_date": "2024-01-15T08:00:00Z",
      "has_poc": true,
      "cwe_ids": ["CWE-120", "CWE-119"],
      "vulnerable_products": [
        "Linux kernel >= 5.4.0 < 5.10.0",
        "Ubuntu 20.04 LTS",
        "CentOS 8.x"
      ]
    },
    {
      "id": "CVE-2024-0002",
      "description": "SQL injection in web application...",
      "cvss_score": 8.6,
      "published_date": "2024-01-14T12:30:00Z",
      "has_poc": false,
      "cwe_ids": ["CWE-89"]
    }
  ]
}
```

**Filter Logic**:
```
- CRITICAL: cvss_score >= 9.0
- HIGH: cvss_score >= 7.0 AND < 9.0
- MEDIUM: cvss_score >= 4.0 AND < 7.0
- LOW: cvss_score < 4.0
```

---

### 2. Get CVE Detail

**Endpoint**: `GET /api/cves/{cve_id}`

**Description**: Retrieve detailed information about a specific CVE.

**Path Parameters**:
- `cve_id` (string, required): CVE identifier (e.g., CVE-2024-1234)

**Request**:
```bash
curl -X GET http://localhost:8000/api/cves/CVE-2024-1234
```

**Response** (200 OK):
```json
{
  "id": "CVE-2024-1234",
  "description": "A flaw was found in the Linux kernel's implementation of the BPF (Berkeley Packet Filter) subsystem...",
  "cvss_score": 8.8,
  "cvss_vector": "CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H",
  "cwe_ids": ["CWE-119", "CWE-416"],
  "published_date": "2024-02-15T10:00:00Z",
  "last_modified_date": "2024-02-15T14:30:00Z",
  "vulnerable_products": [
    "Linux kernel < 6.6.11",
    "Linux kernel >= 6.7 and < 6.7.9",
    "Ubuntu 23.10",
    "Debian 12"
  ],
  "references": [
    {
      "url": "https://nvd.nist.gov/vuln/detail/CVE-2024-1234",
      "source": "NVD"
    },
    {
      "url": "https://lore.kernel.org/all/...",
      "source": "Linux Kernel Mailing List"
    }
  ],
  "has_poc": true,
  "poc_source": "Exploit-DB",
  "poc_language": "C",
  "cache_updated_at": "2024-02-15T15:00:00Z"
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "CVE-2024-9999 not found"
}
```

---

### 3. Get PoC Code

**Endpoint**: `GET /api/cves/{cve_id}/poc`

**Description**: Retrieve exploit/PoC code for a CVE (authentication required).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Path Parameters**:
- `cve_id` (string, required): CVE identifier

**Request**:
```bash
curl -X GET http://localhost:8000/api/cves/CVE-2024-1234/poc \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response** (200 OK):
```json
{
  "cve_id": "CVE-2024-1234",
  "poc_code": "#include <stdio.h>\n#include <unistd.h>...",
  "poc_language": "C",
  "poc_source": "Exploit-DB",
  "disclaimer": "This code is provided as-is for authorized security research and testing only.",
  "risk_level": "HIGH"
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Not authenticated"
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "PoC code not available for CVE-2024-9999"
}
```

---

## Subscription Endpoints

### 1. Subscribe to CVE

**Endpoint**: `POST /api/subscriptions`

**Description**: Subscribe to CVE alerts (save CVE for user).

**Headers**:
```
Authorization: Bearer <access_token>
X-CSRF-Token: <csrf_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "cve_id": "CVE-2024-1234"
}
```

**Response** (201 Created):
```json
{
  "id": 42,
  "user_id": 1,
  "cve_id": "CVE-2024-1234",
  "created_at": "2024-02-15T15:00:00Z"
}
```

**Error Response** (409 Conflict):
```json
{
  "detail": "You are already subscribed to CVE-2024-1234"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/subscriptions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cve_id": "CVE-2024-1234"
  }'
```

---

### 2. Unsubscribe from CVE

**Endpoint**: `DELETE /api/subscriptions/{cve_id}`

**Description**: Remove CVE from subscriptions.

**Headers**:
```
Authorization: Bearer <access_token>
X-CSRF-Token: <csrf_token>
```

**Path Parameters**:
- `cve_id` (string, required): CVE identifier

**Request**:
```bash
curl -X DELETE http://localhost:8000/api/subscriptions/CVE-2024-1234 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN"
```

**Response** (200 OK):
```json
{
  "message": "Unsubscribed from CVE-2024-1234"
}
```

---

### 3. Get Subscriptions

**Endpoint**: `GET /api/subscriptions`

**Description**: Retrieve user's subscribed CVEs.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Results per page (default: 20, max: 50)

**Request**:
```bash
curl -X GET "http://localhost:8000/api/subscriptions?page=1&limit=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response** (200 OK):
```json
{
  "total": 3,
  "page": 1,
  "limit": 20,
  "total_pages": 1,
  "items": [
    {
      "id": "CVE-2024-1234",
      "description": "Buffer overflow in Linux kernel...",
      "cvss_score": 8.8,
      "published_date": "2024-02-15T10:00:00Z",
      "subscribed_at": "2024-02-15T15:00:00Z"
    },
    {
      "id": "CVE-2024-5678",
      "description": "Authentication bypass in Apache...",
      "cvss_score": 9.1,
      "published_date": "2024-02-10T08:00:00Z",
      "subscribed_at": "2024-02-14T12:30:00Z"
    }
  ]
}
```

---

## Admin Endpoints

### 1. Get Audit Logs

**Endpoint**: `GET /admin/audit-logs`

**Description**: Retrieve system audit logs (admin only).

**Headers**:
```
Authorization: Bearer <admin_access_token>
```

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Filter by action: CVE_SEARCH, LOGIN, REGISTER, SUBSCRIBE, etc. |
| `user_id` | integer | Filter by user |
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Results per page (default: 50) |

**Request**:
```bash
curl -X GET "http://localhost:8000/admin/audit-logs?action=LOGIN&page=1&limit=50" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response** (200 OK):
```json
{
  "total": 125,
  "page": 1,
  "limit": 50,
  "total_pages": 3,
  "items": [
    {
      "id": 1001,
      "user_id": 5,
      "action": "LOGIN",
      "endpoint": "/auth/login",
      "method": "POST",
      "status_code": 200,
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2024-02-15T15:30:00Z",
      "request_params": null
    },
    {
      "id": 1000,
      "user_id": 5,
      "action": "CVE_SEARCH",
      "endpoint": "/api/cves",
      "method": "GET",
      "status_code": 200,
      "ip_address": "192.168.1.100",
      "query_params": {"q": "linux", "severity": "CRITICAL"},
      "timestamp": "2024-02-15T15:28:00Z"
    }
  ]
}
```

**Error Response** (403 Forbidden):
```json
{
  "detail": "Admin access required"
}
```

---

### 2. Get Sync Status

**Endpoint**: `GET /admin/sync-status`

**Description**: Retrieve CVE database synchronization status.

**Request**:
```bash
curl -X GET http://localhost:8000/admin/sync-status
```

**Response** (200 OK):
```json
{
  "cve_count": 250347,
  "last_sync": "2024-02-15T14:50:00Z",
  "last_full_sync": "2024-02-14T02:30:00Z",
  "latest_cve_date": "2024-02-15T10:00:00Z",
  "scheduler_status": "running",
  "next_delta_sync": "2024-02-15T15:10:00Z",
  "next_full_sync": "2024-02-16T02:30:00Z",
  "sync_interval_delta_minutes": 10,
  "sync_interval_full_minutes": 1440
}
```

---

### 3. Trigger Manual Sync

**Endpoint**: `POST /admin/sync/trigger`

**Description**: Manually trigger CVE database synchronization (admin only).

**Headers**:
```
Authorization: Bearer <admin_access_token>
X-CSRF-Token: <csrf_token>
```

**Query Parameters** (optional):
- `sync_type` (string): `delta` (default) or `full`

**Request**:
```bash
curl -X POST http://localhost:8000/admin/sync/trigger?sync_type=delta \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN"
```

**Response** (200 OK):
```json
{
  "sync_type": "delta",
  "start_time": "2024-02-15T15:35:00Z",
  "end_time": "2024-02-15T15:35:08Z",
  "duration_seconds": 8,
  "cves_synced": 23,
  "status": "completed",
  "message": "Successfully synced 23 new/updated CVEs"
}
```

---

## Error Responses

### Standard Error Format

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

### Common HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | OK | Successful GET/POST request |
| 201 | Created | User registered, subscription created |
| 400 | Bad Request | Invalid input, validation failed |
| 401 | Unauthorized | Missing/invalid authentication token |
| 403 | Forbidden | Insufficient permissions (not admin) |
| 404 | Not Found | CVE/user not found |
| 409 | Conflict | Duplicate email, already subscribed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |

### Error Response Examples

**Validation Error** (400):
```json
{
  "detail": "Validation error: password must be at least 8 characters"
}
```

**Authentication Error** (401):
```json
{
  "detail": "Not authenticated"
}
```

**Authorization Error** (403):
```json
{
  "detail": "Admin access required"
}
```

**Rate Limit Error** (429):
```json
{
  "detail": "Rate limit exceeded: 100 requests per hour"
}
```

---

## Rate Limiting

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1708093200
```

### Rate Limit Tiers

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Authentication (login) | 10 | 1 hour |
| CVE Search | 100 | 1 hour |
| Other endpoints | 100 | 1 hour |
| Global (unauthenticated) | 1000 | 1 hour |

### Handling Rate Limits

When you receive a 429 status:

```bash
# Wait until X-RateLimit-Reset timestamp before retrying
until_ts=$(curl -I http://localhost:8000/api/cves | grep X-RateLimit-Reset | cut -d' ' -f2)
wait_seconds=$((until_ts - $(date +%s)))
echo "Rate limited. Retry in $wait_seconds seconds"
sleep $wait_seconds
```

---

## Examples

### Complete Search Workflow

```javascript
// JavaScript example using fetch API

const API_URL = 'http://localhost:8000';

async function searchCVEs(query, severity) {
  // 1. Get CSRF token
  const csrfRes = await fetch(`${API_URL}/api/csrf-token`);
  const { csrf_token } = await csrfRes.json();
  
  // 2. Login (if not already logged in)
  const loginRes = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrf_token
    },
    body: JSON.stringify({
      email: 'user@example.com',
      password: 'password123'
    })
  });
  const { access_token } = await loginRes.json();
  localStorage.setItem('token', access_token);
  
  // 3. Search CVEs
  const searchRes = await fetch(
    `${API_URL}/api/cves?q=${query}&severity=${severity}&limit=50`,
    {
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    }
  );
  const results = await searchRes.json();
  console.log(`Found ${results.total} CVEs`);
  
  // 4. Get details for first CVE
  if (results.items.length > 0) {
    const cveId = results.items[0].id;
    const detailRes = await fetch(`${API_URL}/api/cves/${cveId}`, {
      headers: { 'Authorization': `Bearer ${access_token}` }
    });
    const detail = await detailRes.json();
    console.log(detail);
    
    // 5. Subscribe to CVE
    const subRes = await fetch(`${API_URL}/api/subscriptions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${access_token}`,
        'X-CSRF-Token': csrf_token
      },
      body: JSON.stringify({ cve_id: cveId })
    });
    const subscription = await subRes.json();
    console.log('Subscribed:', subscription);
  }
}

searchCVEs('linux', 'CRITICAL');
```

### Python Example using Requests

```python
import requests

API_URL = 'http://localhost:8000'

# Get CSRF token
csrf_res = requests.get(f'{API_URL}/api/csrf-token')
csrf_token = csrf_res.json()['csrf_token']

# Login
headers = {'X-CSRF-Token': csrf_token}
login_res = requests.post(
    f'{API_URL}/auth/login',
    headers=headers,
    json={
        'email': 'user@example.com',
        'password': 'password123'
    }
)
access_token = login_res.json()['access_token']

# Search CVEs
headers['Authorization'] = f'Bearer {access_token}'
search_res = requests.get(
    f'{API_URL}/api/cves',
    params={'q': 'linux', 'severity': 'CRITICAL'},
    headers=headers
)
results = search_res.json()
print(f"Found {results['total']} CVEs")

# Get details
if results['items']:
    cve_id = results['items'][0]['id']
    detail_res = requests.get(
        f'{API_URL}/api/cves/{cve_id}',
        headers=headers
    )
    print(detail_res.json())
```

---

**API Documentation Generated**: 2024-02-15  
**Last Updated**: 2024-02-15  
**Version**: 1.0.0

For interactive API documentation, visit: `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc)
