from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MemoryStore:
    """SQLite-backed memory store for conversation and knowledge entries."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or "data/memory.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        self._connection.commit()

    def add_memory(self, kind: str, content: str, metadata: dict[str, Any] | None = None) -> int:
        cursor = self._connection.execute(
            "INSERT INTO memories (kind, content, metadata) VALUES (?, ?, ?)",
            (kind, content, repr(metadata or {})),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def list_memories(self, kind: str | None = None) -> list[dict[str, Any]]:
        if kind is None:
            rows = self._connection.execute("SELECT id, kind, content, metadata FROM memories ORDER BY id DESC").fetchall()
        else:
            rows = self._connection.execute(
                "SELECT id, kind, content, metadata FROM memories WHERE kind = ? ORDER BY id DESC",
                (kind,),
            ).fetchall()
        return [
            {"id": row[0], "kind": row[1], "content": row[2], "metadata": eval(row[3])}
            for row in rows
        ]

    def close(self) -> None:
        self._connection.close()
