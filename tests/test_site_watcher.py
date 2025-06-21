import sys
import sqlite3
from pathlib import Path
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Provide simple stubs for requests and yaml
requests_stub = types.ModuleType("requests")

def _fake_get(url, headers=None, timeout=10):
    class Resp:
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass
    return Resp(_fake_get.html)

requests_stub.get = _fake_get
sys.modules["requests"] = requests_stub

bs4_stub = types.ModuleType("bs4")

class _Tag:
    def __init__(self, href):
        self._href = href

    def get(self, attr):
        return self._href if attr == "href" else None


class BeautifulSoup:
    def __init__(self, html, parser):
        import re
        self._links = re.findall(r"href=['\"]([^'\"]+)['\"]", html)

    def select(self, selector):
        return [_Tag(h) for h in self._links]

bs4_stub.BeautifulSoup = BeautifulSoup
sys.modules["bs4"] = bs4_stub

yaml_stub = types.ModuleType("yaml")

def _yaml_load(stream):
    text = stream.read() if hasattr(stream, "read") else stream
    lines = [line.rstrip() for line in text.splitlines()]
    sites = []
    current = None
    for line in lines:
        if line.startswith("sites:"):
            continue
        if line.startswith("  - "):
            if current:
                sites.append(current)
            current = {}
            remainder = line[4:]
            if remainder:
                key, value = remainder.split(":", 1)
                current[key.strip()] = value.strip()
        elif line.startswith("    "):
            key, value = line.strip().split(":", 1)
            current[key.strip()] = value.strip()
    if current:
        sites.append(current)
    return {"sites": sites}

yaml_stub.safe_load = _yaml_load
sys.modules["yaml"] = yaml_stub

from detectobot import feed_watcher
from detectobot.agents import site_watcher

entry_hash = feed_watcher.entry_hash
check_and_store = feed_watcher.check_and_store
init_db = feed_watcher.init_db


def test_load_config(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "sites:\n  - name: Example\n    url: http://example.com\n    selector: a\n"
    )
    monkeypatch.setattr(site_watcher, "CONFIG_PATH", str(cfg))
    sites = site_watcher.load_config()
    assert sites == [("Example", "http://example.com", "a")]


def test_get_new_article_links(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "sites:\n  - name: Example\n    url: http://example.com\n    selector: a\n"
    )
    monkeypatch.setattr(site_watcher, "CONFIG_PATH", str(cfg))

    html = "<html><body><a href='p1'>1</a><a href='p2'>2</a></body></html>"
    _fake_get.html = html

    db_path = tmp_path / "db.sqlite"
    links = site_watcher.get_new_article_links(db_path=str(db_path))
    assert links == [
        {"name": "Example", "link": "http://example.com/p1"},
        {"name": "Example", "link": "http://example.com/p2"},
    ]

    # second call should return empty
    links = site_watcher.get_new_article_links(db_path=str(db_path))
    assert links == []
