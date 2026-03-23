"""
app.py — CVE Intel Flask backend

Security hardening implemented:
  1. Strict CVE-ID input validation (regex whitelist, bleach sanitization)
  2. Rate limiting (Flask-Limiter) on every endpoint
  3. Security response headers (CSP, X-Frame-Options, HSTS-ready, etc.)
  4. Parameterized SQL queries (via database.py — zero string interpolation)
  5. No eval(), no dangerouslySetInnerHTML, no exec() anywhere in codebase
"""

import os
import re
import logging
import bleach
from flask import Flask, jsonify, request, render_template, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler
from database import CVEDatabase
from nvd_client import NVDClient

# ------------------------------------------------------------------ #
# Logging                                                              #
# ------------------------------------------------------------------ #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("cve_intel")

# ------------------------------------------------------------------ #
# App init                                                             #
# ------------------------------------------------------------------ #
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32))
app.config["JSON_SORT_KEYS"] = False

# Rate limiting — stored in memory (swap for Redis in production)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["300 per day", "60 per hour"],
    storage_uri="memory://",
)

db  = CVEDatabase()
nvd = NVDClient(api_key=os.environ.get("NVD_API_KEY"))

# ------------------------------------------------------------------ #
# Background scheduler — update NVD every 6 hours                     #
# ------------------------------------------------------------------ #
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(
    nvd.update_recent_cves, "interval", hours=6, args=[db], id="nvd_sync"
)
scheduler.start()

# ------------------------------------------------------------------ #
# Input validation                                                     #
# ------------------------------------------------------------------ #
_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$")


def _validate_cve_id(raw: str) -> str:
    """
    Strict whitelist validation for CVE IDs.
    Only uppercase 'CVE-YYYY-NNNN+' format is accepted.
    """
    if not raw:
        abort(400, description="CVE ID is required.")
    # bleach first, then regex gate
    cleaned = bleach.clean(raw.strip().upper(), tags=[], attributes={}, strip=True)
    if not _CVE_RE.match(cleaned):
        abort(400, description=f"Invalid CVE ID format: '{cleaned}'")
    return cleaned


def _validate_search_query(raw: str) -> str:
    """Sanitize search queries; reject extreme lengths."""
    if not raw or len(raw.strip()) < 2:
        abort(400, description="Search query must be at least 2 characters.")
    if len(raw) > 120:
        abort(400, description="Search query exceeds maximum length (120 chars).")
    return bleach.clean(raw.strip(), tags=[], attributes={}, strip=True)


# ------------------------------------------------------------------ #
# Security response headers (Hardening Measure #2)                    #
# ------------------------------------------------------------------ #
@app.after_request
def add_security_headers(response):
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
    response.headers["Content-Security-Policy"]    = csp
    response.headers["X-Content-Type-Options"]     = "nosniff"
    response.headers["X-Frame-Options"]            = "DENY"
    response.headers["X-XSS-Protection"]           = "1; mode=block"
    response.headers["Referrer-Policy"]            = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]         = "geolocation=(), microphone=(), camera=()"
    return response


# ------------------------------------------------------------------ #
# Error handlers                                                       #
# ------------------------------------------------------------------ #
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": str(e.description)}), 400


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e.description)}), 404


@app.errorhandler(429)
def rate_limited(e):
    return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429


@app.errorhandler(500)
def server_error(e):
    log.exception("Internal server error")
    return jsonify({"error": "Internal server error."}), 500


# ------------------------------------------------------------------ #
# Routes                                                               #
# ------------------------------------------------------------------ #
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/cve/<path:raw_id>")
@limiter.limit("40 per minute; 200 per hour")
def get_cve(raw_id: str):
    """
    Fetch full CVE detail.
    Checks local DB first; falls through to NVD on cache miss.
    """
    cve_id = _validate_cve_id(raw_id)

    # Cache hit
    cached = db.get_cve(cve_id)
    if cached:
        cached["cache"] = "HIT"
        return jsonify(cached)

    # Cache miss → live NVD fetch
    fresh = nvd.fetch_cve(cve_id)
    if not fresh:
        abort(404, description=f"CVE '{cve_id}' not found in NVD or local database.")

    db.store_cve(fresh)
    fresh["cache"] = "MISS"
    return jsonify(fresh)


@app.route("/api/cve/<path:raw_id>/refresh")
@limiter.limit("5 per minute; 20 per hour")
def refresh_cve(raw_id: str):
    """Force a live re-fetch from NVD and update the local cache."""
    cve_id = _validate_cve_id(raw_id)
    fresh = nvd.fetch_cve(cve_id)
    if not fresh:
        abort(404, description=f"CVE '{cve_id}' not found in NVD.")
    db.store_cve(fresh)
    fresh["cache"] = "REFRESHED"
    return jsonify(fresh)


@app.route("/api/search")
@limiter.limit("30 per minute")
def search():
    """Search CVEs by ID prefix or full-text description."""
    query   = _validate_search_query(request.args.get("q", ""))
    limit   = min(int(request.args.get("limit", 25)), 50)
    results = db.search_cves(query, limit=limit)
    return jsonify({"query": query, "count": len(results), "results": results})


@app.route("/api/recent")
@limiter.limit("20 per minute")
def recent():
    """Return recently published CVEs from local DB."""
    limit   = min(int(request.args.get("limit", 30)), 50)
    results = db.get_recent_cves(limit=limit)
    return jsonify({"count": len(results), "results": results})


@app.route("/api/stats")
@limiter.limit("20 per minute")
def stats():
    """Return database statistics."""
    return jsonify(db.get_stats())


@app.route("/api/trigger-update")
@limiter.limit("2 per hour")
def trigger_update():
    """Manually trigger an NVD sync (rate-limited)."""
    count = nvd.update_recent_cves(db, days_back=1)
    return jsonify({"message": f"Update complete. {count} CVEs processed."})


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    # Never use debug=True in production
    app.run(host="127.0.0.1", port=5000, debug=False)
