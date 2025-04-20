import sqlite3
from pathlib import Path
from detectabot.feed_watcher import entry_hash, check_and_store, init_db

def test_entry_hash_uniqueness():
    entry1 = {"link": "https://example.com/1"}
    entry2 = {"link": "https://example.com/2"}
    assert entry_hash(entry1) != entry_hash(entry2)

def test_check_and_store(tmp_path):
    db_path = tmp_path / "db.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_entries (
            hash TEXT PRIMARY KEY,
            feed_name TEXT,
            entry_title TEXT,
            entry_link TEXT,
            timestamp INTEGER
        )
    """)
    entry = {"link": "https://example.com/unique"}
    h = entry_hash(entry)
    assert check_and_store(conn, h, "Test Feed", entry) is True
    # Second insert should be False (duplicate)
    assert check_and_store(conn, h, "Test Feed", entry) is False
