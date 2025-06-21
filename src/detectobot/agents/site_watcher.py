import os
import yaml
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from detectobot import feed_watcher as core

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config.yaml'))
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../site_watcher.db'))


def load_config():
    """Load site configuration from YAML file."""
    with open(CONFIG_PATH, 'r') as f:
        cfg = yaml.safe_load(f)
    sites = []
    for site in cfg.get('sites', []):
        name = site.get('name')
        url = site.get('url')
        selector = site.get('selector', 'a')
        if name and url:
            sites.append((name, url, selector))
    return sites


def get_new_article_links(db_path: str = DB_PATH):
    """Return unseen article links from configured websites."""
    sites = load_config()
    conn = sqlite3.connect(db_path)
    core.init_db(conn)
    new_links = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

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
            h = core.entry_hash(entry)
            if core.check_and_store(conn, h, name, entry):
                new_links.append({'name': name, 'link': abs_link})

    conn.close()
    return new_links


if __name__ == '__main__':
    for item in get_new_article_links():
        print(f"--- {item['name']} ---\n- {item['link']}\n")
