import sqlite3
from pathlib import Path
import importlib.util

module_path = Path(__file__).parent.parent / "src" / "detectobot" / "feed_watcher.py"
spec = importlib.util.spec_from_file_location("feed_watcher", module_path)
feed_watcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed_watcher)

entry_hash = feed_watcher.entry_hash
check_and_store = feed_watcher.check_and_store
init_db = feed_watcher.init_db

def test_entry_hash_uniqueness():
    entry1 = {"link": "https://example.com/1"}
    entry2 = {"link": "https://example.com/2"}
    assert entry_hash(entry1) != entry_hash(entry2)

def test_check_and_store(tmp_path):
    db_path = tmp_path / "db.sqlite"
    conn = sqlite3.connect(db_path)
    init_db(conn)
    entry = {"link": "https://example.com/unique"}
    h = entry_hash(entry)
    assert check_and_store(conn, h, "Test Feed", entry) is True
    # Second insert should be False (duplicate)
    assert check_and_store(conn, h, "Test Feed", entry) is False
