# Syntax Validation Quick Reference

**TL;DR**: Run validation before commit, or pre-commit hook will block you.

---

## One-Minute Validation

```bash
# Quick check (cross-platform)
python scripts/validate_syntax.py

# Expected output: ✅ All syntax valid!
```

---

## Before Each Commit

```bash
# Option 1: Python script (all platforms)
python scripts/validate_syntax.py

# Option 2: Bash script (Linux/macOS)
bash scripts/validate-syntax.sh

# Option 3: Windows batch
.\scripts\validate-syntax.bat
```

**If validation fails**: Don't commit. Fix the errors first.

---

## Common Commands

| Task | Command | Platform |
|------|---------|----------|
| Validate all | `python scripts/validate_syntax.py` | All |
| Validate Python only | `python -m py_compile backend/` | All |
| Validate JS only | `npm run lint` | All |
| Single Python file | `python -m py_compile backend/app.py` | All |
| Single JS file | `node -c frontend/src/main.jsx` | All |

---

## Most Common Syntax Errors

### Python

```python
# ❌ Missing colon
def my_function()
    return True

# ✅ Fix
def my_function():
    return True

# ❌ Wrong indentation (mixed spaces/tabs)
def func():
  x = 1  # 2 spaces (should be 4)
    return x  # 4 spaces

# ✅ Fix (use 4 spaces consistently)
def func():
    x = 1
    return x

# ❌ Unmatched bracket
def func():
    items = [1, 2, 3
    return items

# ✅ Fix
def func():
    items = [1, 2, 3]
    return items
```

### JavaScript

```javascript
// ❌ Unclosed tag
function App() {
  return <div><Button

// ✅ Fix
function App() {
  return <div><Button /></div>
}

// ❌ Missing import
function MyComponent() {
  return <div>{someFunction()}</div>
}

// ✅ Fix
import { someFunction } from './utils'
function MyComponent() {
  return <div>{someFunction()}</div>
}

// ❌ Invalid prop syntax
<Button disabled=true />

// ✅ Fix
<Button disabled={true} />
// Or
<Button disabled />
```

---

## Error Messages Explained

| Message | Meaning | Fix |
|---------|---------|-----|
| `SyntaxError: invalid syntax` | Code structure wrong | Check colons, brackets, indentation |
| `IndentationError: unexpected indent` | Wrong indentation level | Use 4 spaces for Python |
| `SyntaxError: unexpected EOF` | Unmatched brackets | Count all `(`, `[`, `{` |
| `SyntaxError: Invalid JSX` | Broken React tag | Close all `<Tag>` with `</Tag>` |
| `NameError: name ... is not defined` | Missing import | Add import statement |

---

## Validation Before PR

✅ **Checklist**
- [ ] Run `python scripts/validate_syntax.py`
- [ ] Result: All files valid
- [ ] No syntax errors in terminal
- [ ] Ready to commit

---

## If Validation Fails Locally

**Step 1**: Read the error message carefully
```
❌ backend/models/cve.py (line 42)
   SyntaxError: invalid syntax
   
   def search_cves(query
                        ^
```

**Step 2**: Find the line mentioned (line 42)

**Step 3**: Look for common issues:
- Missing `:` after `def`/`if`/`for`/`class`
- Unmatched `(`, `[`, `{`
- Wrong indentation
- Unclosed `""` or `''` or `` ` ``
- Unclosed JSX tag `<Component>`

**Step 4**: Fix the issue

**Step 5**: Run validation again
```bash
python scripts/validate_syntax.py
```

---

## Getting Help

| Issue | Action |
|-------|--------|
| Don't understand error | Read error message carefully, check line number |
| Error on specific line | Look at that exact line and surrounding code |
| Can't find the issue | Try validating one file at a time |
| Still stuck | Ask in PR comments or GitHub Discussions |

---

## Important Reminders

⚠️ **CRITICAL**:
1. **Syntax validation is REQUIRED** - Not optional
2. **Pre-commit hook will block commits** - No way around it
3. **CI/CD will reject PRs** - Can't merge without passing
4. **Errors are easy to fix** - Most are simple: missing colon, wrong indent, etc.

---

## Quick Links

- 📖 [Full Syntax Requirements](./SYNTAX_REQUIREMENTS.md)
- 📝 [Contributing Guide](./CONTRIBUTING.md#syntax-requirements)
- 🐛 [Report Issues](./CONTRIBUTING.md#reporting-issues)
- 💬 [Get Help](./CONTRIBUTING.md#getting-help)

---

## Examples That Fail Validation

```bash
$ python scripts/validate_syntax.py

❌ backend/services/nvd_sync.py (line 15)
   SyntaxError: invalid syntax
   def fetch_cves(limit
                      ^

Found 1 error. Exit code: 1
```

### Fix:
```python
# Change line 15 from:
def fetch_cves(limit

# To:
def fetch_cves(limit: int):
```

Then rerun:
```bash
$ python scripts/validate_syntax.py

✅ All syntax valid! 
✅ 22 Python files OK
✅ 17 JavaScript files OK
Success! Exit code: 0
```

---

## Examples That Pass Validation

✅ All these are valid:

```python
# Python
def search_cves(query: str, limit: int = 20) -> List[CVE]:
    """Search for CVEs with filters."""
    return db.query(CVE).filter(CVE.description.ilike(f"%{query}%")).limit(limit).all()

class CVEService:
    """Service for CVE operations."""
    
    def __init__(self, db: Session):
        self.db = db
```

```javascript
// JavaScript
function CVESearch({ onSearch }) {
  const [query, setQuery] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query);
  };
  
  return <input onChange={(e) => setQuery(e.target.value)} />;
}
```

---

## Bookmark This File

📌 Save this for quick reference:
- **URL**: `SYNTAX_QUICK_REFERENCE.md` in repo root
- **Use**: When you see syntax errors
- **Time**: Takes 2 minutes to understand any error

---

**Last Updated**: March 19, 2026  
**Validity**: All information is current and enforced by pre-commit hooks + CI/CD
