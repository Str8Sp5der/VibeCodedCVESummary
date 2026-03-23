# CVE Database - Secure Cybersecurity Professional Tool

![React](https://img.shields.io/badge/React-18.2.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)

A comprehensive, security-hardened web application for cybersecurity professionals to search, analyze, and track CVE (Common Vulnerabilities and Exposures) data with automatic database updates, proof-of-concept code retrieval, and user alert management.

## 🚀 Features

- **CVE Search & Analysis**: Search from 150,000+ CVEs with real-time filtering by severity, year, and keywords
- **Detailed CVE Information**: View CVSS scores, CWE classifications, vulnerable products, and references
- **Proof of Concept (PoC) Code**: Secure access to exploit code with security warnings and authentication
- **User Subscriptions**: Subscribe to CVE alerts and maintain a personal watchlist
- **Automatic Database Updates**: Background jobs sync CVE data from NVD API every 10-60 minutes
- **User Authentication**: Secure JWT-based authentication with role-based access control
- **Audit Logging**: Complete request tracking for security compliance
- **Responsive Web UI**: Modern, intuitive interface built with React
- **Production-Ready**: Containerized with Docker, secure by default

## 🏗️ Architecture

```
VIBECodeProject/
├── backend/                      # FastAPI microservice
│   ├── app.py                   # FastAPI main application
│   ├── config.py                # Environment configuration
│   ├── database.py              # SQLAlchemy database setup
│   ├── security.py              # JWT, password hashing, encryption
│   ├── schemas.py               # Pydantic request/response models
│   ├── dependencies.py          # FastAPI dependency injection
│   ├── models/
│   │   ├── cve.py              # CVE ORM model
│   │   ├── user.py             # User authentication model
│   │   ├── audit_log.py        # Audit logging model
│   │   └── subscription.py     # User CVE subscriptions
│   ├── routes/
│   │   ├── auth.py             # Registration, login, token endpoints
│   │   ├── cves.py             # CVE search and detail endpoints
│   │   └── admin.py            # Admin-only audit and sync endpoints
│   ├── services/
│   │   ├── nvd_sync.py         # NVD API data sync service
│   │   ├── exploit_sync.py     # Exploit-DB PoC correlation
│   │   └── scheduler.py        # APScheduler background jobs
│   ├── middleware/
│   │   └── audit_logger.py     # Request audit logging
│   ├── tests/                   # Pytest test suites
│   └── requirements.txt         # Python dependencies
│
├── frontend/                     # React + Vite SPA
│   ├── src/
│   │   ├── App.jsx             # Main application component
│   │   ├── main.jsx            # React entry point
│   │   ├── components/
│   │   │   ├── Navbar.jsx      # Navigation bar
│   │   │   ├── PrivateRoute.jsx # Protected route wrapper
│   │   │   └── PoCViewer.jsx   # Secure PoC code viewer
│   │   ├── hooks/
│   │   │   ├── useCVEs.js      # React Query CVE data hooks
│   │   │   └── useAuth.js      # Authentication state hook
│   │   ├── pages/
│   │   │   ├── CVESearchPage.jsx     # CVE search interface
│   │   │   ├── CVEDetailPage.jsx     # CVE detail view
│   │   │   ├── LoginPage.jsx         # User login form
│   │   │   ├── RegisterPage.jsx      # User registration form
│   │   │   └── Dashboard.jsx         # User dashboard
│   │   ├── api/
│   │   │   ├── client.js       # Axios HTTP client
│   │   │   └── endpoints.js    # API endpoint definitions
│   │   └── utils/
│   │       └── csrf.js         # CSRF token management
│   ├── package.json
│   ├── vite.config.js
│   ├── vitest.config.js
│   └── index.html
│
├── database/
│   └── init_db.py              # Database initialization script
│
├── docs/
│   ├── README.md               # This file
│   ├── SECURITY.md             # Security documentation
│   ├── API_REFERENCE.md        # API endpoint documentation
│   └── DEPLOYMENT.md           # Deployment guide
│
├── Dockerfile.backend           # Python 3.11 FastAPI container
├── Dockerfile.frontend          # Node.js build + Nginx container
├── docker-compose.yml           # Multi-container orchestration
├── nginx.conf                   # Nginx reverse proxy config
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## 🔒 Security Features

### Input Validation
- **CVE ID Format**: Strict regex validation (`CVE-\d{4}-\d{4,}`)
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy ORM
- **Pydantic Schemas**: All inputs validated against strict schemas

### Authentication & Authorization
- **JWT Tokens**: HttpOnly cookies + Bearer tokens, 24-hour expiration
- **Password Security**: bcrypt hashing with salt
- **Role-Based Access Control**: admin, analyst, viewer roles
- **CSRF Protection**: Token-based cross-site request forgery prevention

### XSS & Content Security
- **DOMPurify**: HTML sanitization for all user-generated content
- **CSP Headers**: Content-Security-Policy restricts script execution
- **Highlight.js**: Automatic escaping for code blocks

### Data Protection
- **Encryption**: Fernet symmetric encryption for sensitive fields (PoC code)
- **HTTPS Ready**: Strict-Transport-Security and secure cookie flags
- **No Hardcoded Secrets**: All credentials in environment variables

### Audit & Monitoring
- **Request Logging**: All API calls logged with user, IP, timestamp, status
- **Rate Limiting**: 100 requests/hour per user, 1000/hour global
- **Brute Force Prevention**: 10 login attempts/hour limit

## 🚦 Getting Started

### Prerequisites
- Docker & Docker Compose (recommended)
- OR: Python 3.11+, Node.js 18+, PostgreSQL 15

### Quick Start with Docker

1. **Clone and setup**:
```bash
cd VIBECodeProject
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. **Configure credentials** (edit `backend/.env`):
```bash
# Get free NVD API key from https://services.nvd.nist.gov/rest/json/cves/2.0
NVD_API_KEY=your-nvd-api-key-here
JWT_SECRET_KEY=your-secret-key-change-in-production
```

3. **Start all services**:
```bash
docker-compose up --build
```

4. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

### Manual Setup (Local Development)

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python -m database.init_db  # Initialize database
uvicorn app:app --reload --port 8000
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:3000
```

## 📚 API Documentation

### Authentication Endpoints

**Register User**:
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}

Response: 201 Created
{
  "user": { "id": 1, "email": "...", "role": "viewer", ... },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Login**:
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

### CVE Endpoints

**Search CVEs**:
```bash
GET /api/cves?q=RCE&severity=CRITICAL&page=1&limit=50

Response: 200 OK
{
  "total": 145,
  "items": [
    {
      "id": "CVE-2024-1234",
      "description": "Remote Code Execution vulnerability in...",
      "cvss_score": 9.8,
      "published_date": "2024-02-15T00:00:00",
      "has_poc": true,
      "vulnerable_products": [...],
      ...
    }
  ],
  "page": 1,
  "limit": 50,
  "total_pages": 3
}
```

**Get CVE Details**:
```bash
GET /api/cves/CVE-2024-1234

Response: 200 OK
{
  "id": "CVE-2024-1234",
  "description": "...",
  "cvss_score": 9.8,
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "cwe_ids": ["CWE-89", "CWE-79"],
  "vulnerable_products": ["product:x.x", ...],
  "references": [{"url": "https://...", "source": "..."}],
  "poc_code": "#!/bin/bash\n..." (if has_poc),
  ...
}
```

**Subscribe to CVE**:
```bash
POST /api/subscriptions
Authorization: Bearer {token}
Content-Type: application/json

{
  "cve_id": "CVE-2024-1234"
}

Response: 201 Created
```

### Admin Endpoints

**Get Audit Logs** (admin only):
```bash
GET /admin/audit-logs?page=1&limit=100
Authorization: Bearer {admin-token}

Response: 200 OK
{
  "total": 1523,
  "items": [
    {
      "id": 1,
      "user_id": 5,
      "action": "GET /api/cves",
      "status_code": 200,
      "timestamp": "2024-02-15T12:30:45",
      "ip_address": "192.168.1.100"
    }
  ],
  ...
}
```

**Get Sync Status**:
```bash
GET /admin/sync-status
Authorization: Bearer {admin-token}

Response: 200 OK
{
  "cve_count": 147523,
  "latest_cve_date": "2024-02-15T10:00:00",
  "scheduler_status": "running",
  "jobs": [
    {"id": "delta_sync", "name": "Delta CVE sync (recent CVEs)", "next_run_time": "2024-02-15T12:15:00"},
    {"id": "full_sync", "name": "Full CVE sync (paginated)", "next_run_time": "2024-02-15T13:00:00"}
  ]
}
```

Full API documentation available at `http://localhost:8000/docs` (Swagger UI) or in [API_REFERENCE.md](docs/API_REFERENCE.md).

## 🔐 Security Compliance

### OWASP Top 10 Mitigation
- ✅ **A1: Injection** → Parameterized queries, input validation
- ✅ **A2: Authentication** → JWT, bcrypt, CSRF tokens
- ✅ **A3: Sensitive Data** → Encryption, HTTPS, secure cookies
- ✅ **A4: XML/XXE** → No XML processing
- ✅ **A5: Broken Access Control** → Role-based authorization
- ✅ **A6: Security Misconfiguration** → Security headers, .env secrets
- ✅ **A7: XSS** → DOMPurify, CSP headers, output escaping
- ✅ **A8: Broken Authentication** → Secure sessions, rate limiting
- ✅ **A9: SSRF** → URL validation on references
- ✅ **A10: Insufficient Logging** → Comprehensive audit logging

See [SECURITY.md](docs/SECURITY.md) for detailed vulnerability analysis.

## 📊 Performance

- **CVE Search**: <500ms for 50 results on local PostgreSQL
- **Concurrent Users**: Handles 100+ concurrent users with <10s response time
- **Database Queries**: Optimized with indexes on `cve_id`, `severity`, `published_date`
- **Caching**: React Query client-side caching, 5-10 min stale time

See [PERFORMANCE.md](docs/PERFORMANCE.md) for benchmarking results.

## 🧪 Testing

**Backend Tests**:
```bash
cd backend
pytest tests/ -v --cov=. --cov-report=html
```

**Frontend Tests**:
```bash
cd frontend
npm run test
```

Test coverage targets: **≥80% backend, ≥70% frontend**

## 🚀 Deployment

### Production with Docker
```bash
# Build production images
docker build -t cve-app-backend:latest -f Dockerfile.backend .
docker build -t cve-app-frontend:latest -f Dockerfile.frontend .

# Use docker-compose.prod.yml for production
docker-compose -f docker-compose.yml up -d
```

### Environment Variables (Production)
```bash
DEBUG=False
DATABASE_URL=postgresql://user:pass@prod-db-host:5432/cve_db
JWT_SECRET_KEY=<strong-random-key>
NVD_API_KEY=<your-nvd-key>
FRONTEND_URL=https://cve-app.example.com
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment guide.

## 📝 License

This project is provided for educational and professional use in cybersecurity analysis.

## 👥 Support

For issues, security vulnerabilities, or questions:
- Check [FAQ](docs/FAQ.md)
- Review [SECURITY.md](docs/SECURITY.md) for security-related questions
- See [API_REFERENCE.md](docs/API_REFERENCE.md) for API usage

## 📅 Changelog

**v1.0.0** (Initial Release)
- ✅ CVE search and filtering
- ✅ User authentication with JWT
- ✅ Automatic NVD database sync
- ✅ PoC code retrieval
- ✅ User subscriptions
- ✅ Audit logging
- ✅ Docker containerization
- ✅ Comprehensive security hardening

---

**Built with ❤️ for cybersecurity professionals**
