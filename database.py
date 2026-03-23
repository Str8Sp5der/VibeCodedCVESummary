"""
database.py — CVE Intel local SQLite store
All queries use parameterized statements. No string interpolation in SQL.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/cve_database.db")
log = logging.getLogger(__name__)


class CVEDatabase:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ------------------------------------------------------------------ #
    # Connection                                                           #
    # ------------------------------------------------------------------ #
    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    # ------------------------------------------------------------------ #
    # Schema                                                               #
    # ------------------------------------------------------------------ #
    def _init_schema(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS cves (
                    id               TEXT PRIMARY KEY,
                    description      TEXT NOT NULL DEFAULT '',
                    published        TEXT,
                    modified         TEXT,
                    cvss_v3          TEXT,
                    cvss_v2          TEXT,
                    affected_systems TEXT,
                    refs             TEXT,
                    cwes             TEXT,
                    poc              TEXT,
                    severity         TEXT DEFAULT 'UNKNOWN',
                    cvss_score       REAL DEFAULT 0.0,
                    source           TEXT DEFAULT 'NVD',
                    fetched_at       TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_published  ON cves(published  DESC);
                CREATE INDEX IF NOT EXISTS idx_severity   ON cves(severity);
                CREATE INDEX IF NOT EXISTS idx_cvss_score ON cves(cvss_score DESC);
                CREATE INDEX IF NOT EXISTS idx_fetched    ON cves(fetched_at DESC);

                CREATE VIRTUAL TABLE IF NOT EXISTS cves_fts USING fts5(
                    id,
                    description,
                    content=cves,
                    content_rowid=rowid
                );

                CREATE TRIGGER IF NOT EXISTS cves_ai AFTER INSERT ON cves BEGIN
                    INSERT INTO cves_fts(rowid, id, description)
                    VALUES (new.rowid, new.id, new.description);
                END;

                CREATE TRIGGER IF NOT EXISTS cves_au AFTER UPDATE ON cves BEGIN
                    INSERT INTO cves_fts(cves_fts, rowid, id, description)
                    VALUES ('delete', old.rowid, old.id, old.description);
                    INSERT INTO cves_fts(rowid, id, description)
                    VALUES (new.rowid, new.id, new.description);
                END;

                CREATE TABLE IF NOT EXISTS update_log (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp    TEXT,
                    cves_updated INTEGER,
                    success      INTEGER
                );
            """)

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #
    def store_cve(self, data: dict):
        """Upsert a CVE record. All values parameterized."""
        severity = "UNKNOWN"
        score = 0.0
        if data.get("cvss_v3"):
            severity = data["cvss_v3"].get("severity", "UNKNOWN")
            score = float(data["cvss_v3"].get("score", 0))
        elif data.get("cvss_v2"):
            severity = data["cvss_v2"].get("severity", "UNKNOWN")
            score = float(data["cvss_v2"].get("score", 0))

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO cves
                    (id, description, published, modified, cvss_v3, cvss_v2,
                     affected_systems, refs, cwes, poc, severity, cvss_score,
                     source, fetched_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    description      = excluded.description,
                    modified         = excluded.modified,
                    cvss_v3          = excluded.cvss_v3,
                    cvss_v2          = excluded.cvss_v2,
                    affected_systems = excluded.affected_systems,
                    refs             = excluded.refs,
                    cwes             = excluded.cwes,
                    poc              = excluded.poc,
                    severity         = excluded.severity,
                    cvss_score       = excluded.cvss_score,
                    fetched_at       = excluded.fetched_at
                """,
                (
                    data["id"],
                    data.get("description", ""),
                    data.get("published", ""),
                    data.get("modified", ""),
                    json.dumps(data.get("cvss_v3")),
                    json.dumps(data.get("cvss_v2")),
                    json.dumps(data.get("affected_systems", [])),
                    json.dumps(data.get("refs", [])),
                    json.dumps(data.get("cwes", [])),
                    json.dumps(data.get("poc", [])),
                    severity,
                    score,
                    data.get("source", "NVD"),
                    data.get("fetched_at", datetime.utcnow().isoformat()),
                ),
            )

    def log_update(self, count: int, success: bool):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO update_log (timestamp, cves_updated, success) VALUES (?,?,?)",
                (datetime.utcnow().isoformat(), count, 1 if success else 0),
            )

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #
    def get_cve(self, cve_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM cves WHERE id = ?", (cve_id,)
            ).fetchone()
        return self._full(row) if row else None

    def search_cves(self, query: str, limit: int = 25) -> list[dict]:
        with self._conn() as conn:
            # Direct CVE-ID prefix search
            if query.upper().startswith("CVE-"):
                rows = conn.execute(
                    "SELECT * FROM cves WHERE id LIKE ? ORDER BY published DESC LIMIT ?",
                    (f"{query.upper()}%", limit),
                ).fetchall()
            else:
                # Full-text search on description + id
                try:
                    rows = conn.execute(
                        """
                        SELECT c.* FROM cves c
                        JOIN cves_fts f ON c.rowid = f.rowid
                        WHERE cves_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                        """,
                        (query, limit),
                    ).fetchall()
                except Exception:
                    rows = conn.execute(
                        "SELECT * FROM cves WHERE description LIKE ? LIMIT ?",
                        (f"%{query}%", limit),
                    ).fetchall()
        return [self._summary(r) for r in rows]

    def get_recent_cves(self, limit: int = 30) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM cves ORDER BY published DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._summary(r) for r in rows]

    def get_stats(self) -> dict:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM cves").fetchone()[0]
            sev_rows = conn.execute(
                "SELECT severity, COUNT(*) FROM cves GROUP BY severity"
            ).fetchall()
            last = conn.execute(
                "SELECT timestamp FROM update_log ORDER BY id DESC LIMIT 1"
            ).fetchone()
            top = conn.execute(
                "SELECT id, cvss_score, severity FROM cves ORDER BY cvss_score DESC LIMIT 5"
            ).fetchall()
        return {
            "total_cves": total,
            "by_severity": {r[0]: r[1] for r in sev_rows},
            "last_updated": last[0] if last else None,
            "top_critical": [dict(r) for r in top],
        }

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_json_fields(d: dict, fields: list[str]) -> dict:
        for f in fields:
            if d.get(f):
                try:
                    d[f] = json.loads(d[f])
                except Exception:
                    d[f] = None
        return d

    def _full(self, row) -> dict:
        d = dict(row)
        return self._parse_json_fields(
            d, ["cvss_v3", "cvss_v2", "affected_systems", "refs", "cwes", "poc"]
        )

    def _summary(self, row) -> dict:
        d = dict(row)
        d = self._parse_json_fields(d, ["cvss_v3", "cvss_v2"])
        for f in ["affected_systems", "refs", "cwes", "poc"]:
            d.pop(f, None)
        return d
