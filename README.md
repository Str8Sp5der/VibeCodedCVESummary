# CVE Intel — Vulnerability Intelligence Platform

A security-hardened CVE lookup tool built for cybersecurity professionals. Search any CVE, get full CVSS scoring, affected systems, proof-of-concept exploits, and references — all sourced from MITRE CVE API with a local auto-updating database.

---

## Features

- **Live MITRE CVE lookup** — Fetches from MITRE CVE API on cache miss
- **Local SQLite database** — Persistent CVE storage with FTS5 full-text search
- **Auto-update** — APScheduler syncs latest CVEs from NVD every 6 hours
- **PoC aggregation** — Searches ExploitDB and nomi-sec/PoC-in-GitHub index
- **Animated CVSS gauge** — Visual score display with v3/v2 metric breakdown
- **Affected systems** — CPE configuration parsing with vendor/product/version
- **Security hardened** — Rate limiting, CSP headers, strict input validation, parameterized SQL

---

## Quick Start

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd cve_tracker

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Set NVD API key for higher rate limits
#    Get free key at: https://nvd.nist.gov/developers/request-an-api-key
export NVD_API_KEY="your-key-here"

# 4. Run the app
# Activate the virtual environment (Windows)
.\.venv\Scripts\activate
# Then run
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

---

## Project Structure

```
cve_tracker/
├── app.py              # Flask backend, routes, rate limiting, security headers
├── database.py         # SQLite wrapper — all queries parameterized
├── nvd_client.py       # NVD API v2.0 client + ExploitDB + GitHub PoC scraping
├── requirements.txt
├── SECURITY.md         # Security Manifesto (assignment deliverable)
├── README.md
├── data/
│   └── cve_database.db # Auto-created SQLite database
└── templates/
    └── index.html      # Full-stack frontend (HTML/CSS/JS)
```

---

## API Endpoints

| Method | Endpoint | Description | Rate Limit |
|---|---|---|---|
| GET | `/` | Web UI | — |
| GET | `/api/cve/<CVE-ID>` | Full CVE detail | 40/min |
| GET | `/api/cve/<CVE-ID>/refresh` | Force re-fetch from NVD | 5/min |
| GET | `/api/search?q=<query>` | Search local DB | 30/min |
| GET | `/api/recent?limit=N` | Recent CVEs | 20/min |
| GET | `/api/stats` | DB statistics | 20/min |
| GET | `/api/trigger-update` | Manual NVD sync | 2/hr |

---

## Security Architecture

See [SECURITY.md](SECURITY.md) for full details. Summary:

1. **Input Validation** — Strict `CVE-YYYY-NNNNN` regex on all CVE IDs; `bleach` sanitization on all query params; `textContent`-only DOM insertion on frontend
2. **Rate Limiting** — Per-endpoint limits via Flask-Limiter, 429 responses on breach
3. **Parameterized SQL** — Zero string interpolation in any database query
4. **Security Headers** — CSP, X-Frame-Options, X-XSS-Protection on every response
5. **No dangerous functions** — No `eval()`, no `exec()`, no `dangerouslySetInnerHTML`

---

## NVD API Key

Without an API key, NVD enforces a 5 requests/30 seconds rate limit. With a free key:
- 50 requests per 30 seconds
- Recommended for production use
- Apply at: https://nvd.nist.gov/developers/request-an-api-key

---

## Responsible Use

This tool is for **authorized security research and penetration testing only**. PoC exploit information is sourced from public databases (ExploitDB, GitHub) and presented for defensive purposes. Do not use exploit code against systems you do not own or have written permission to test.

---

## Built With

- Flask, SQLite (FTS5), APScheduler, Requests, BeautifulSoup4, Bleach
- Frontend: Vanilla JS, Syne + JetBrains Mono + DM Sans fonts, SVG CVSS gauge
- Data: MITRE CVE API, ExploitDB JSON API, nomi-sec/PoC-in-GitHub
