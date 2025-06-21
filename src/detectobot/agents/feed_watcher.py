"""Feed watcher utilities used by agents."""
import os
import sqlite3
import feedparser
from typing import List, Tuple, Dict

from ..core.db_utils import init_db, entry_hash, check_and_store, DB_PATH

# Path to configuration file; can be overridden in tests
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config.yaml'))


def load_config(config_path: str | None = None) -> List[Tuple[str, str]]:
    """Return list of (name, url) tuples from the feeds section."""
    if config_path is None:
        config_path = CONFIG_PATH
    with open(config_path, "r") as f:
        text = f.read()
    feeds = []
    current = None
    for line in text.splitlines():
        line = line.rstrip()
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
    return [(f.get("name"), f.get("url")) for f in feeds]


def get_latest_article_links(config_path: str | None = None) -> List[Dict[str, str]]:
    """Return the latest article link from each configured feed."""
    feeds = load_config(config_path) if config_path is not None else load_config()
    links: List[Dict[str, str]] = []
    for name, url in feeds:
        parsed = feedparser.parse(url)
        entries = getattr(parsed, 'entries', [])
        if entries:
            link = entries[0].get('link')
            if link:
                links.append({'name': name, 'link': link})
    return links


def get_new_article_links(db_path: str = DB_PATH, config_path: str | None = None) -> List[Dict[str, str]]:
    """Return unseen article links from all configured feeds."""
    conn = sqlite3.connect(db_path)
    init_db(conn)
    new_links: List[Dict[str, str]] = []
    feeds = load_config(config_path) if config_path is not None else load_config()
    for name, url in feeds:
        parsed = feedparser.parse(url)
        for entry in getattr(parsed, 'entries', []):
            h = entry_hash(entry)
            if check_and_store(conn, h, name, entry):
                link = entry.get('link')
                if link:
                    new_links.append({'name': name, 'link': link})
    conn.close()
    return new_links

