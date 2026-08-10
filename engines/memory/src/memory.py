"""
NEXUS Memory Engine v0.3

Backed by SQLite so stored memories survive a process restart.
store/retrieve/forget/all are unchanged from v0.2. New in v0.3:
recent() for browsing/searching history without touching those.
"""

import json
import os
import sqlite3


class MemoryEngine:
    def __init__(self, db_path="data/memory.db"):
        self.db_path = db_path

        if db_path != ":memory:":
            directory = os.path.dirname(db_path)
            if directory:
                os.makedirs(directory, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def store(self, key, value):
        self.conn.execute(
            """
            INSERT INTO memory (key, value, updated_at)
            VALUES (?, ?, strftime('%Y-%m-%d %H:%M:%f', 'now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, json.dumps(value)),
        )
        self.conn.commit()

    def retrieve(self, key):
        row = self.conn.execute(
            "SELECT value FROM memory WHERE key = ?", (key,)
        ).fetchone()

        return json.loads(row[0]) if row else None

    def forget(self, key):
        self.conn.execute("DELETE FROM memory WHERE key = ?", (key,))
        self.conn.commit()

    def all(self):
        rows = self.conn.execute("SELECT key, value FROM memory").fetchall()
        return {key: json.loads(value) for key, value in rows}

    def recent(self, prefix=None, contains=None, limit=50):
        """Recent entries as [{key, value, updated_at}, ...], most
        recent first. Optionally filtered to keys starting with
        `prefix`, and/or to entries where `contains` appears in the
        key or the value (case-insensitive)."""
        query = "SELECT key, value, updated_at FROM memory WHERE 1=1"
        params = []
        if prefix:
            query += " AND key LIKE ?"
            params.append(f"{prefix}%")
        if contains:
            query += " AND (LOWER(key) LIKE ? OR LOWER(value) LIKE ?)"
            term = f"%{contains.lower()}%"
            params.extend([term, term])
        query += " ORDER BY updated_at DESC, rowid DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        return [
            {"key": key, "value": json.loads(value), "updated_at": updated_at}
            for key, value, updated_at in rows
        ]

    def close(self):
        self.conn.close()
