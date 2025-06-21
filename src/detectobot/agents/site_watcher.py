"""Website watcher utilities used by agents."""
import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Tuple, Dict


from ..core.db_utils import init_db, entry_hash, check_and_store, DB_PATH

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config.yaml'))


def load_config(config_path: str | None = None) -> List[Tuple[str, str, str]]:
    """Return list of (name, url, selector) tuples from the sites section."""
    if config_path is None:
        config_path = CONFIG_PATH
    with open(config_path, "r") as f:
        import yaml
        cfg = yaml.safe_load(f)
    sites = cfg.get('sites', [])
    return [(s['name'], s['url'], s.get('selector', 'a')) for s in sites]


def get_new_article_links(db_path: str = DB_PATH, config_path: str | None = None) -> List[Dict[str, str]]:
    """Return unseen article links from configured websites."""
    conn = sqlite3.connect(db_path)
    init_db(conn)
    new_links: List[Dict[str, str]] = []
    headers = {"User-Agent": "Mozilla/5.0"}
    sites = load_config(config_path) if config_path is not None else load_config()
    for name, url, selector in sites:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
        except Exception:
            continue
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.select(selector):
            link = a.get('href')
            if not link:
                continue
            abs_link = urljoin(url, link)
            entry = {'link': abs_link}
            h = entry_hash(entry)
            if check_and_store(conn, h, name, entry):
                new_links.append({'name': name, 'link': abs_link})
    conn.close()
    return new_links

