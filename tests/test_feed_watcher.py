import sys
import sqlite3
from pathlib import Path
import types

# Allow importing modules from the src directory without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Provide a minimal feedparser stub so agent modules can be imported without the
# actual dependency present in the environment.
feedparser_stub = types.ModuleType("feedparser")
feedparser_stub.parse = lambda url: {"entries": []}
sys.modules.setdefault("feedparser", feedparser_stub)

yaml_stub = types.ModuleType("yaml")

def _simple_yaml_load(stream):
    text = stream.read() if hasattr(stream, "read") else stream
    lines = [line.rstrip() for line in text.splitlines()]
    feeds = []
    current = None
    for line in lines:
        if line.startswith("feeds:"):
            continue
        if line.startswith("  - "):
            if current:
                feeds.append(current)
            current = {}
            remainder = line[4:]
            if remainder:
                key, value = remainder.split(":", 1)
                current[key.strip()] = value.strip()
        elif line.startswith("    "):
            key, value = line.strip().split(":", 1)
            current[key.strip()] = value.strip()
    if current:
        feeds.append(current)
    return {"feeds": feeds}

yaml_stub.safe_load = _simple_yaml_load
sys.modules.setdefault("yaml", yaml_stub)

from detectobot import feed_watcher
from detectobot.agents import feed_watcher as agent_feed_watcher

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


def test_load_config(tmp_path, monkeypatch):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "feeds:\n  - name: MyFeed\n    url: http://example.com/rss\n"
    )
    monkeypatch.setattr(agent_feed_watcher, "CONFIG_PATH", str(cfg))
    feeds = agent_feed_watcher.load_config()
    assert feeds == [("MyFeed", "http://example.com/rss")]


def test_get_latest_article_links(monkeypatch):
    monkeypatch.setattr(
        agent_feed_watcher,
        "load_config",
        lambda: [("LocalFeed", "http://does-not-matter")],
    )

    class FakeFeed:
        def __init__(self, entries):
            self.entries = entries

    def fake_parse(url):
        return FakeFeed([{"link": "https://example.com/local"}])

    monkeypatch.setattr(agent_feed_watcher.feedparser, "parse", fake_parse)
    links = agent_feed_watcher.get_latest_article_links()
    assert links == [{"name": "LocalFeed", "link": "https://example.com/local"}]


def test_get_new_article_links(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "feeds:\n  - name: LocalFeed\n    url: http://example.com/rss\n"
    )
    monkeypatch.setattr(agent_feed_watcher, "CONFIG_PATH", str(cfg))

    class FakeFeed:
        def __init__(self, entries):
            self.entries = entries

    def fake_parse(url):
        return FakeFeed([
            {"link": "https://example.com/new1", "title": "t"},
            {"link": "https://example.com/new2", "title": "t"},
        ])

    monkeypatch.setattr(agent_feed_watcher.feedparser, "parse", fake_parse)

    db_path = tmp_path / "db.sqlite"

    links = agent_feed_watcher.get_new_article_links(db_path=str(db_path))
    assert links == [
        {"name": "LocalFeed", "link": "https://example.com/new1"},
        {"name": "LocalFeed", "link": "https://example.com/new2"},
    ]

    # Second call should return empty list since entries are stored
    links = agent_feed_watcher.get_new_article_links(db_path=str(db_path))
    assert links == []
