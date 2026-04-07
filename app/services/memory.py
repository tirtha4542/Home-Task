"""SQLite-backed chat history storage."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from app.models.schemas import ChatMessage


@dataclass(slots=True)
class StoredMessage:
    """Internal representation of a stored chat message."""

    role: str
    content: str
    created_at: datetime

    def to_schema(self) -> ChatMessage:
        """Convert the stored message to the public API schema."""

        return ChatMessage(
            role=self.role,
            content=self.content,
            created_at=self.created_at,
        )


class SQLiteMemoryStore:
    """Persistent memory store keyed by session ID."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self._lock = Lock()

    def initialize(self) -> None:
        """Create the database file and schema if they do not exist."""

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_session_id_id
                ON messages (session_id, id)
                """
            )
            connection.commit()

    def append_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        """Persist one message and return its normalized representation."""

        created_at = datetime.now(timezone.utc)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, created_at.isoformat()),
            )
            connection.commit()

        return ChatMessage(role=role, content=content, created_at=created_at)

    def get_history(self, session_id: str) -> list[ChatMessage]:
        """Return ordered history for a single session."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        history: list[ChatMessage] = []
        for row in rows:
            history.append(
                StoredMessage(
                    role=row["role"],
                    content=row["content"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                ).to_schema()
            )
        return history

    def clear_history(self, session_id: str) -> int:
        """Delete all messages for a session and return the number removed."""

        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (session_id,),
            )
            connection.commit()
            return cursor.rowcount

    def healthcheck(self) -> bool:
        """Verify the database is reachable."""

        try:
            with self._connect() as connection:
                connection.execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error:
            return False

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection configured for dict-style rows."""

        connection = sqlite3.connect(self.database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

