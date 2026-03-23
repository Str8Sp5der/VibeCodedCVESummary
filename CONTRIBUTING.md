# Contributing to CVE Database Application

Thank you for your interest in contributing to the CVE Database Application! This document outlines how to contribute effectively.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Syntax Requirements](#syntax-requirements)
6. [Git Workflow](#git-workflow)
7. [Testing Requirements](#testing-requirements)
8. [Documentation](#documentation)
9. [Security Considerations](#security-considerations)
10. [Submitting Changes](#submitting-changes)

---

## Code of Conduct

### Our Commitment

We are committed to providing a welcoming and inspiring community for all. Please read and adhere to our [Code of Conduct](./CODE_OF_CONDUCT.md).

### Expected Behavior

- Be respectful and inclusive
- Use welcoming language
- Focus on constructive feedback
- Respect differing opinions
- Report unacceptable behavior

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (optional)
- Git 2.30+

### Setup Development Environment

```bash
# 1. Fork and clone repository
git clone https://github.com/your-username/cve-database.git
cd cve-database

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# 4. Setup frontend
cd ../frontend
npm install

# 5. Create environment files
cp ../.env.example ../.env
# Edit .env with your settings

# 6. Start development servers
# Terminal 1:
cd backend
uvicorn app:app --reload

# Terminal 2:
cd frontend
npm run dev
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
# From main branch
git pull origin main

# Create feature branch (use descriptive name)
git checkout -b feature/add-export-functionality
# or
git checkout -b bugfix/fix-search-pagination
# or
git checkout -b docs/update-api-reference
```

### 2. Make Changes

```bash
# Edit files, add features, fix bugs

# Stage changes
git add .

# Commit with clear message
git commit -m "feat: add CSV export functionality

- Add export endpoint to CVE API
- Implement CSV generation utility
- Add tests for export functionality
- Update documentation"
```

### 3. Test Changes

```bash
# Backend tests
cd backend
pytest --cov=. --cov-report=html

# Frontend tests
cd frontend
npm run test -- --coverage

# Integration tests
cd backend
pytest tests/test_integration.py
```

### 4. Push and Create Pull Request

```bash
# Push feature branch
git push origin feature/add-export-functionality

# Create PR on GitHub with:
# - Clear description of changes
# - Reference to related issues
# - Test evidence
# - Screenshots/videos (if UI changes)
```

---

## Coding Standards

### Backend (Python)

#### Style Guide: PEP 8

```python
# ✅ GOOD
def search_cves(query: str, severity: str = "ALL", limit: int = 20) -> Dict[str, Any]:
    """Search CVEs with filters.
    
    Args:
        query: Search text
        severity: Severity filter (CRITICAL, HIGH, MEDIUM, LOW, ALL)
        limit: Max results (max 50)
    
    Returns:
        Dictionary with total count and CVE list
    """
    results = db.query(CVE).filter(CVE.description.ilike(f"%{query}%"))
    if severity != "ALL":
        results = results.filter(CVE.severity == severity)
    return {"total": results.count(), "items": results.limit(limit).all()}

# ❌ BAD
def search(q, s="ALL", l=20):
    result = db.query(CVE).filter(CVE.description.ilike(f"%{q}%"))
    if s != "ALL":
        result = result.filter(CVE.severity == s)
    return {"total": result.count(), "items": result.limit(l).all()}
```

#### Type Hints Required

```python
from typing import Dict, List, Optional, Any

# Always use type hints
def get_user_id(email: str) -> Optional[int]:
    """Get user ID by email."""
    user = db.query(User).filter(User.email == email).first()
    return user.id if user else None
```

#### Naming Conventions

```python
# Constants: UPPER_SNAKE_CASE
MAX_CVE_RESULTS = 50
DEFAULT_PAGE_SIZE = 20

# Functions/methods: lower_snake_case
def validate_cve_id(cve_id: str) -> bool:
    pass

# Classes: PascalCase
class CVESearchService:
    pass

# Private attributes: _leading_underscore
class User:
    def __init__(self, email: str):
        self._email = email
```

#### Documentation Standards

```python
def create_subscription(user_id: int, cve_id: str) -> Subscription:
    """Create a CVE subscription for user.
    
    Args:
        user_id: Unique user identifier
        cve_id: CVE identifier (e.g., CVE-2024-1234)
    
    Returns:
        Created Subscription object
    
    Raises:
        UserNotFound: If user doesn't exist
        DuplicateSubscription: If already subscribed
    
    Example:
        >>> sub = create_subscription(user_id=1, cve_id="CVE-2024-1234")
        >>> print(sub.created_at)
    """
    pass
```

### Frontend (JavaScript/React)

#### Style Guide: Airbnb JavaScript

```javascript
// ✅ GOOD - Functional component with hooks
import React, { useState, useEffect } from 'react';
import useAuth from '../hooks/useAuth';

export function CVESearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const { user } = useAuth();
  
  const handleSearch = (event) => {
    event.preventDefault();
    // Search logic
  };
  
  return (
    <div>
      <form onSubmit={handleSearch}>
        <input 
          value={query} 
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search CVEs..."
        />
        <button type="submit">Search</button>
      </form>
      <ul>
        {results.map(cve => (
          <li key={cve.id}>{cve.id}</li>
        ))}
      </ul>
    </div>
  );
}

// ❌ BAD - Old class component, unclear naming
class SearchComp extends React.Component {
  constructor(props) {
    super(props);
    this.state = { q: '', r: [] };
  }
  
  handleClick = () => {
    this.setState({ r: [] });
  };
  
  render() {
    return <div><input value={this.state.q} /><button onClick={this.handleClick}>Go</button></div>;
  }
}
```

#### Naming Conventions

```javascript
// Constants: UPPER_SNAKE_CASE
const API_TIMEOUT = 30000;
const DEFAULT_PAGE_SIZE = 20;

// Functions/variables: camelCase
function getCVEDetail(cveId) {
  return fetch(`/api/cves/${cveId}`);
}

// Components: PascalCase
function CVESearchPage() {
  return <div>Search</div>;
}

// Private functions: _leading_underscore
function _sanitizeInput(input) {
  return input.trim();
}
```

#### Component Structure

```javascript
// ✅ GOOD structure
import React, { useState } from 'react';
import PropTypes from 'prop-types';

/**
 * SearchBar component for CVE search input
 * @component
 */
export function SearchBar({ onSearch, placeholder = 'Search CVEs...' }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input 
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        aria-label="CVE search input"
      />
      <button type="submit">Search</button>
    </form>
  );
}

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
  placeholder: PropTypes.string,
};
```

---

## Syntax Requirements

### ⚠️ CRITICAL: All Code Must Pass Syntax Validation

**All code MUST be syntactically correct before submission.** Syntax errors will block merge to main branch.

### Syntax Validation is Mandatory

Starting immediately, all code contributions must:
1. ✅ Pass Python syntax validation (`py_compile`)
2. ✅ Pass JavaScript syntax validation (Node.js `-c` flag)
3. ✅ Pass linting checks (ESLint, Pylint)
4. ✅ Pass type checking (MyPy, TypeScript)

**Failure to meet these requirements will result in automatic PR rejection.**

### Automated Syntax Checking

#### Pre-Commit Hook (Local)

Before committing, syntax is checked automatically. To set up:

```bash
# Copy pre-commit hook template
cp .github/pre-commit-hook .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**What happens**: When you commit, the hook automatically validates all Python and JavaScript files. If any fail, the commit is rejected with clear error messages.

#### CI/CD Pipeline (Remote)

GitHub Actions automatically validates on all PRs:
- Runs on every push
- Blocks merge if validation fails
- Shows detailed error reports

### Manual Syntax Validation

Run validation scripts locally before committing:

#### Python and JavaScript (Cross-Platform)

```bash
# Use Python validator (recommended)
python scripts/validate_syntax.py

# Output:
# ✅ Validating Python files...
# ✅ app.py
# ✅ database.py
# ❌ models/invalid.py: SyntaxError on line 42
# 
# Summary: 22 valid, 1 error
# Exit code: 1 (fail)
```

#### Linux/macOS Only

```bash
bash scripts/validate-syntax.sh
```

#### Windows Only

```bash
.\scripts\validate-syntax.bat
```

#### Manual Python Validation

```bash
# Single file
python -m py_compile backend/app.py

# All Python files
find backend -name "*.py" -exec python -m py_compile {} +

# Or using loop
for file in $(find backend -name "*.py"); do
    python -m py_compile "$file"
done
```

#### Manual JavaScript Validation

```bash
# Single file
node -c frontend/src/main.jsx

# All JavaScript files
for file in $(find frontend/src -name "*.js" -o -name "*.jsx"); do
    node -c "$file"
done
```

### Common Syntax Errors

#### Python

| Error | Cause | Fix |
|-------|-------|-----|
| `SyntaxError: invalid syntax` | Missing colon after function def | `def func():` not `def func()` |
| `IndentationError: unexpected indent` | Inconsistent indentation | Use 4 spaces consistently |
| `SyntaxError: unexpected EOF` | Unclosed bracket/parenthesis | Check all `(`, `[`, `{` are closed |
| `SyntaxError: invalid character` | Non-ASCII character in code | Check encoding, use only ASCII |
| `NameError: name` not defined | Import missing or misspelled | Add missing import statement |

```python
# ❌ Missing colon
def search_cves(query)
    return db.query(CVE)

# ✅ Correct
def search_cves(query):
    return db.query(CVE)
```

#### JavaScript

| Error | Cause | Fix |
|-------|-------|-----|
| `SyntaxError: Unexpected token` | Missing semicolon or bracket | Complete statement |
| `SyntaxError: Unexpected identifier` | Missing `const`/`let`/`var` | Declare variable |
| `SyntaxError: Unexpected token '}'` | Unmatched braces | Count braces carefully |
| `SyntaxError: Invalid JSX` | Unclosed tag or invalid props | Close all JSX tags |

```javascript
// ❌ Missing closing tag
function App() {
  return <div><Component

// ✅ Correct
function App() {
  return <div><Component /></div>
}
```

### Validation Standards

#### Python Standards

| Standard | Requirement | Example |
|----------|-------------|---------|
| **Python Version** | 3.11+ | `python --version` |
| **Indentation** | 4 spaces | Never tabs |
| **Line Length** | Max 120 chars | Split long lines |
| **Imports** | At top, sorted | `from` imports after regular imports |
| **Type Hints** | Required for all functions | `def func(x: int) -> bool:` |
| **Naming** | snake_case for functions | `def my_function():` |
| **Docstrings** | For all public functions | Use triple quotes |

#### JavaScript Standards

| Standard | Requirement | Example |
|----------|-------------|---------|
| **Node Version** | 18+ | `node --version` |
| **Indentation** | 2 spaces | Never tabs, never 4 spaces |
| **Line Length** | Max 100 chars | Split long lines |
| **Imports** | ES6 modules | `import { func } from './module'` |
| **Semicolons** | End statements | Mostly automatic with Prettier |
| **Naming** | camelCase for functions | `function myFunction()` |
| **Components** | PascalCase | `function MyComponent()` |
| **JSX** | Close all tags | `<Component />` not `<Component>` |

### Validation Checklist Before Submitting PR

- [ ] **Python files validated**: `python scripts/validate_syntax.py`
- [ ] **No syntax errors reported**
- [ ] **Linting checks pass**: `npm run lint`
- [ ] **Type checking passes**: `mypy backend` (if configured)
- [ ] **No hardcoded imports of non-existent modules**
- [ ] **All brackets/braces matched**: `{`, `}`, `[`, `]`, `(`, `)`
- [ ] **Proper indentation throughout**
- [ ] **All JSX tags properly closed**
- [ ] **No console errors/warnings on local test**

### What Happens If Syntax Fails

1. **Local Commit**: Pre-commit hook blocks commit, shows error details
2. **Pre-Push**: CI/CD checks fail, explains what needs fixing
3. **Pull Request**: GitHub Actions blocks merge with detailed report
4. **Automated Response**: Bot comments on PR with error links

### Example Error Report

```
❌ SYNTAX VALIDATION FAILED

File: backend/models/cve.py
Line: 42
Error: SyntaxError: invalid syntax

    41: class CVE(Base):
 >  42:     def search_cves(query
    43:         """Search for CVEs"""
    
Problem: Missing closing parenthesis on function definition
Solution: Change line 42 to: def search_cves(query):
```

### Disabling Syntax Checks (NOT RECOMMENDED)

You should NEVER disable syntax checks, but if absolutely necessary:

```bash
# Force commit (NOT RECOMMENDED - will be caught in CI/CD)
git commit --no-verify
```

**WARNING**: This will fail in CI/CD and block PR merge. Don't do this.

### Syntax Requirements Documentation

For complete details, see [SYNTAX_REQUIREMENTS.md](./SYNTAX_REQUIREMENTS.md)

---

## Git Workflow

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style change (formatting, semicolons)
- `refactor`: Code refactoring without feature/fix
- `perf`: Performance improvement
- `test`: Test addition or update
- `chore`: Build, dependency, or tooling changes
- `ci`: CI configuration changes

#### Scope

- `api`: Backend API changes
- `frontend`: Frontend changes
- `db`: Database changes
- `security`: Security-related changes
- `ci/cd`: Deployment/CI changes

#### Subject

- Use imperative mood ("add feature" not "adds feature")
- Don't capitalize first letter
- No period at end
- Max 50 characters

#### Body

- Explain what and why, not how
- Wrap at 72 characters
- Reference issues: `Fixes #123`, `Relates to #456`

#### Examples

```
feat(api): add CVE export endpoint

- Implement CSV export for search results
- Add endpoint POST /api/cves/export
- Support filtering by severity and date range

Fixes #145
```

```
fix(frontend): correct pagination button styling

The next/previous buttons had incorrect spacing on mobile.

Fixes #201
```

---

## Testing Requirements

### Minimum Test Coverage

- **Backend**: ≥80% code coverage
- **Frontend**: ≥70% component coverage
- All new features must have tests
- All bug fixes must include regression tests

### Running Tests

```bash
# Backend
cd backend
pytest --cov=. --cov-report=html

# Frontend
cd frontend
npm run test -- --coverage

# Check coverage
# Backend: htmlcov/index.html
# Frontend: coverage/index.html
```

### Test File Naming

```
tests/
├── unit/
│   ├── test_auth.py
│   ├── test_validation.py
│   └── test_security.py
├── integration/
│   ├── test_cve_sync.py
│   └── test_user_workflow.py
└── e2e/
    └── test_searchworkflow.js
```

---

## Documentation

### Code Comments

```python
# ❌ BAD - Obvious what code does
x = x + 1  # Increment x

# ✅ GOOD - Explains why
user_attempts += 1  # Track consecutive failed login attempts for rate limiting
```

### Docstrings

```python
# Required for all public functions/classes
def validate_cve_id(cve_id: str) -> bool:
    """Validate CVE ID format (CVE-YYYY-NNNN).
    
    Args:
        cve_id: CVE identifier to validate
    
    Returns:
        True if valid format, False otherwise
    """
    import re
    return bool(re.match(r'^CVE-\d{4}-\d{4,}$', cve_id))
```

### README Updates

- Update README.md if changing feature behavior
- Add new configuration options to .env.example
- Document breaking changes in CHANGELOG.md

---

## Security Considerations

### Before Submitting

1. **No Hardcoded Secrets**
   ```python
   # ❌ BAD
   API_KEY = "sk_live_1234567890abcdef"
   
   # ✅ GOOD
   API_KEY = os.getenv("API_KEY")
   ```

2. **Input Validation**
   ```python
   # Always validate user input
   if not validate_cve_id(user_input):
       raise ValueError("Invalid CVE ID format")
   ```

3. **SQL Injection Prevention**
   ```python
   # ❌ BAD
   query = f"SELECT * FROM cves WHERE id = '{user_input}'"
   
   # ✅ GOOD
   query = db.query(CVE).filter(CVE.id == user_input)
   ```

4. **XSS Prevention (Frontend)**
   ```javascript
   // ❌ BAD
   <div dangerouslySetInnerHTML={{ __html: userInput }} />
   
   // ✅ GOOD
   import DOMPurify from 'dompurify';
   <div>{DOMPurify.sanitize(userInput)}</div>
   ```

5. **CSRF Protection**
   - Always include CSRF token in POST/PUT/DELETE requests
   - Validate on backend

6. **Rate Limiting**
   - Check for rate limit middleware on sensitive endpoints
   - Implement exponential backoff for retries

---

## Submitting Changes

### Pull Request Checklist

- [ ] Branch created from `main`
- [ ] Code follows style guide
- [ ] Tests added/updated (≥80% coverage)
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] No breaking changes (or documented)
- [ ] Commit messages follow format
- [ ] PR description is clear

### PR Description Template

```markdown
## Description
Brief description of changes

## Related Issues
Fixes #123
Relates to #456

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No console errors/warnings
- [ ] Features work as intended
```

### Review Process

1. Automated checks must pass (tests, linting)
2. At least 2 approvals from maintainers
3. Features reviewed for security
4. Performance impact assessed
5. Documentation reviewed

---

## Reporting Issues

### Bug Report

```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: Ubuntu 22.04
- Python: 3.11
- Browser: Chrome 121

## Error Message
```
Error traceback here
```
```

### Feature Request

```markdown
## Description
Clear description of the feature

## Use Case
Why is this needed?

## Proposed Solution
How should it work?

## Alternatives
Other approaches considered
```

---

## Getting Help

- 📖 Read [README.md](../README.md)
- 📚 Check [API_REFERENCE.md](./docs/API_REFERENCE.md)
- 💬 Ask in GitHub Discussions
- 🐛 File an issue for bugs

---

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

---

**Thank you for contributing!** 🙌

Your efforts help make the CVE Database Application better for the entire community.

For questions, contact: dev@example.com
