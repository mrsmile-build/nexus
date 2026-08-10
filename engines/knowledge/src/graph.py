"""
NEXUS Knowledge Graph Engine v0.3

Backed by SQLite so nodes and edges survive a process restart. All
method names and return shapes match v0.2 exactly, so query.py and
infer.py need no changes beyond their import fix.
"""

import json
import os
import sqlite3


class KnowledgeGraph:
    def __init__(self, db_path="data/knowledge.db"):
        self.db_path = db_path

        if db_path != ":memory:":
            directory = os.path.dirname(db_path)
            if directory:
                os.makedirs(directory, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                name TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                relation TEXT NOT NULL,
                target TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    @property
    def nodes(self):
        rows = self.conn.execute("SELECT name, data FROM nodes").fetchall()
        return {name: json.loads(data) for name, data in rows}

    @property
    def edges(self):
        rows = self.conn.execute(
            "SELECT source, relation, target FROM edges"
        ).fetchall()
        return [{"source": s, "relation": r, "target": t} for s, r, t in rows]

    def add_node(self, name, data=None):
        if not self.exists(name):
            self.conn.execute(
                "INSERT INTO nodes (name, data) VALUES (?, ?)",
                (name, json.dumps(data or {})),
            )
            self.conn.commit()

    def add_edge(self, source, relation, target):
        self.add_node(source)
        self.add_node(target)

        self.conn.execute(
            "INSERT INTO edges (source, relation, target) VALUES (?, ?, ?)",
            (source, relation, target),
        )
        self.conn.commit()

    def neighbors(self, node):
        rows = self.conn.execute(
            "SELECT source, relation, target FROM edges WHERE source = ?",
            (node,),
        ).fetchall()
        return [{"source": s, "relation": r, "target": t} for s, r, t in rows]

    def related(self, node):
        rows = self.conn.execute(
            """
            SELECT target FROM edges WHERE source = ?
            UNION
            SELECT source FROM edges WHERE target = ?
            """,
            (node, node),
        ).fetchall()
        return sorted(row[0] for row in rows)

    def search(self, keyword):
        escaped = keyword.lower().replace("%", r"\%").replace("_", r"\_")
        rows = self.conn.execute(
            "SELECT name FROM nodes WHERE LOWER(name) LIKE ? ESCAPE '\\'",
            (f"%{escaped}%",),
        ).fetchall()
        return sorted(row[0] for row in rows)

    def exists(self, node):
        row = self.conn.execute(
            "SELECT 1 FROM nodes WHERE name = ?", (node,)
        ).fetchone()
        return row is not None

    def relation_exists(self, source, relation, target):
        row = self.conn.execute(
            """
            SELECT 1 FROM edges
            WHERE source = ? AND relation = ? AND target = ?
            """,
            (source, relation, target),
        ).fetchone()
        return row is not None

    def remove_node(self, node):
        self.conn.execute("DELETE FROM nodes WHERE name = ?", (node,))
        self.conn.execute(
            "DELETE FROM edges WHERE source = ? OR target = ?", (node, node)
        )
        self.conn.commit()

    def remove_edge(self, source, relation, target):
        self.conn.execute(
            "DELETE FROM edges WHERE source = ? AND relation = ? AND target = ?",
            (source, relation, target),
        )
        self.conn.commit()

    def show(self):
        return {"nodes": self.nodes, "edges": self.edges}

    def close(self):
        self.conn.close()
