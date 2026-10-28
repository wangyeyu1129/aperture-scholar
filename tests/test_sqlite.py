import pytest

from aperture_scholar.domain.models import Paper
from aperture_scholar.infrastructure.sqlite import (
    SQLiteCardRepository,
    SQLiteDatabase,
    SQLitePaperRepository,
    SQLiteResponseCache,
)


@pytest.fixture
def database(tmp_path):
    database = SQLiteDatabase(tmp_path / "nested" / "test.sqlite3")
    database.initialize()
    database.initialize()
    return database


def test_upsert_roundtrip_and_sql_injection_safety(database):
    repository = SQLitePaperRepository(database)
    paper = Paper(id="p'; DROP TABLE papers;--", title="First")
    repository.upsert(paper)
    repository.upsert(paper.model_copy(update={"title": "Updated"}))
    assert repository.get(paper.id).title == "Updated"
    assert repository.get("missing") is None


def test_cards_idempotent_and_roundtrip(database, card):
    repository = SQLiteCardRepository(database)
    repository.save([card, card])
    assert repository.list_cards() == [card]


def test_cache_ttl_and_overwrite(database):
    now = [100.0]
    cache = SQLiteResponseCache(database, clock=lambda: now[0])
    assert cache.get("key") is None
    cache.put("key", "one", 10)
    assert cache.get("key") == "one"
    now[0] = 110
    assert cache.get("key") is None
    cache.put("key", "two", 20)
    assert cache.get("key") == "two"
    with pytest.raises(ValueError):
        cache.put("key", "invalid", 0)


def test_newer_schema_rejected(database):
    with database.connect() as connection:
        connection.execute("PRAGMA user_version=99")
    with pytest.raises(RuntimeError):
        database.initialize()


def test_transaction_rolls_back_and_connection_closes(database):
    import sqlite3

    with pytest.raises(RuntimeError), database.connect() as connection:
        connection.execute("INSERT INTO papers VALUES (?, ?)", ("rollback", "{}"))
        raise RuntimeError("abort")
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")
    with database.connect() as reopened:
        assert reopened.execute("SELECT count(*) FROM papers").fetchone()[0] == 0
