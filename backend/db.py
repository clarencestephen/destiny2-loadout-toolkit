"""Tiny SQLite-backed store for Discord ↔ Bungie link state.

Two tables:
  pending  (code, discord_id, expires_at)  — short-lived one-time codes
  links    (discord_id PRIMARY KEY, bungie_id, display_name, linked_at)
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from threading import Lock


class LinkStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path, isolation_level=None, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    def _init_db(self) -> None:
        with self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS pending (
                  code        TEXT PRIMARY KEY,
                  discord_id  TEXT NOT NULL,
                  expires_at  INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS links (
                  discord_id    TEXT PRIMARY KEY,
                  bungie_id     TEXT NOT NULL,
                  display_name  TEXT NOT NULL DEFAULT '',
                  linked_at     INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS links_bungie_idx ON links (bungie_id);
                """
            )

    def save_pending(self, code: str, discord_id: str, expires_at: int) -> None:
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO pending (code, discord_id, expires_at) VALUES (?, ?, ?)",
                (code, discord_id, expires_at),
            )

    def consume_pending(self, code: str) -> dict | None:
        now = int(time.time())
        with self._lock, self._conn() as c:
            row = c.execute(
                "SELECT discord_id, expires_at FROM pending WHERE code = ?",
                (code,),
            ).fetchone()
            if not row:
                return None
            c.execute("DELETE FROM pending WHERE code = ?", (code,))
            if row["expires_at"] < now:
                return None
            return {"discord_id": row["discord_id"], "expires_at": row["expires_at"]}

    def save_link(self, discord_id: str, bungie_id: str, display_name: str, linked_at: int) -> None:
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO links (discord_id, bungie_id, display_name, linked_at)"
                " VALUES (?, ?, ?, ?)",
                (discord_id, bungie_id, display_name, linked_at),
            )

    def lookup_by_discord(self, discord_id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT discord_id, bungie_id, display_name, linked_at FROM links WHERE discord_id = ?",
                (discord_id,),
            ).fetchone()
            return dict(row) if row else None

    def lookup_by_bungie(self, bungie_id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT discord_id, bungie_id, display_name, linked_at FROM links WHERE bungie_id = ?",
                (bungie_id,),
            ).fetchone()
            return dict(row) if row else None
