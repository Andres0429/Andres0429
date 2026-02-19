from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class Storage:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    property_key TEXT NOT NULL,
                    config_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (property_key, config_hash)
                )
                """
            )

    def get_cache(self, property_key: str, config_hash: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM cache_entries WHERE property_key=? AND config_hash=?",
                (property_key, config_hash),
            ).fetchone()
            if not row:
                return None
            return json.loads(row[0])

    def set_cache(self, property_key: str, config_hash: str, payload: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache_entries (property_key, config_hash, payload_json)
                VALUES (?, ?, ?)
                """,
                (property_key, config_hash, json.dumps(payload)),
            )
