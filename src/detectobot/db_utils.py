import hashlib
import time
import sqlite3

def entry_hash(entry: dict) -> str:
    """Return a stable SHA-256 hash for a feed or site entry."""
    link = entry.get("link", "")
    return hashlib.sha256(link.encode("utf-8")).hexdigest()


def init_db(conn):
    """Ensure the seen_entries table exists."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_entries (
            hash TEXT PRIMARY KEY,
            feed_name TEXT,
            entry_title TEXT,
            entry_link TEXT,
            timestamp INTEGER
        )
        """
    )
    conn.commit()


def check_and_store(conn, h: str, feed_name: str, entry: dict) -> bool:
    """Insert the entry if unseen and return True. Return False if already seen."""
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM seen_entries WHERE hash = ?", (h,))
    if cur.fetchone():
        return False
    cur.execute(
        """
        INSERT INTO seen_entries (hash, feed_name, entry_title, entry_link, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (h, feed_name, entry.get("title"), entry.get("link"), int(time.time())),
    )
    conn.commit()
    return True
