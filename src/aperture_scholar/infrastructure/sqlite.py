"""Small transactional SQLite adapters; explicit initialization, no import-time I/O."""

import sqlite3
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from aperture_scholar.domain.models import IdeaCard, Paper


class SQLiteDatabase:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Commit/rollback and always close, including when a statement fails."""
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version > 1:
                raise RuntimeError("database schema is newer than this application")
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS papers (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS cards (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY, payload TEXT NOT NULL, expires_at REAL NOT NULL
                );
                PRAGMA user_version=1;
                """
            )


class SQLitePaperRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def upsert(self, paper: Paper) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO papers VALUES (?, ?) ON CONFLICT(id) "
                "DO UPDATE SET payload=excluded.payload",
                (paper.id, paper.model_dump_json()),
            )

    def get(self, paper_id: str) -> Paper | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT payload FROM papers WHERE id=?", (paper_id,)
            ).fetchone()
        return Paper.model_validate_json(row[0]) if row else None


class SQLiteCardRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def save(self, cards: Sequence[IdeaCard]) -> None:
        with self.database.connect() as connection:
            connection.executemany(
                "INSERT INTO cards VALUES (?, ?) ON CONFLICT(id) "
                "DO UPDATE SET payload=excluded.payload",
                [(card.idea.id, card.model_dump_json()) for card in cards],
            )

    def list_cards(self) -> list[IdeaCard]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT payload FROM cards ORDER BY id").fetchall()
        return [IdeaCard.model_validate_json(row[0]) for row in rows]


class SQLiteResponseCache:
    def __init__(self, database: SQLiteDatabase, clock: Callable[[], float] = time.time) -> None:
        self.database, self.clock = database, clock

    def get(self, key: str) -> str | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT payload FROM cache WHERE key=? AND expires_at>?",
                (key, self.clock()),
            ).fetchone()
        return str(row[0]) if row else None

    def put(self, key: str, payload: str, ttl_seconds: float) -> None:
        if ttl_seconds <= 0:
            raise ValueError("cache TTL must be positive")
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO cache VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET "
                "payload=excluded.payload, expires_at=excluded.expires_at",
                (key, payload, self.clock() + ttl_seconds),
            )
