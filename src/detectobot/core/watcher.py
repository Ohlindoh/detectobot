"""Website and feed monitoring functionality."""
import os
import sqlite3
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .db_utils import init_db, entry_hash, check_and_store
from .config import load_config

# Use the DB_PATH from db_utils
from .db_utils import DB_PATH

def get_new_feed_links(db_path: str = DB_PATH):
    """Return unseen article links for all configured RSS feeds."""
    feeds = load_config('feeds')
    conn = sqlite3.connect(db_path)
    init_db(conn)
    new_articles = []
    for feed in feeds:
        name = feed['name']
        url = feed['url']
        parsed = feedparser.parse(url)
        for entry in getattr(parsed, "entries", []):
            h = entry_hash(entry)
            if check_and_store(conn, h, name, entry):
                link = entry.get("link")
                if link:
                    new_articles.append({"name": name, "link": link})
    conn.close()
    return new_articles


def get_new_site_links(db_path: str = DB_PATH):
    """Return unseen article links from configured websites (HTML scraping)."""
    sites = load_config('sites')
    conn = sqlite3.connect(db_path)
    init_db(conn)
    new_links = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    for site in sites:
        name = site.get('name')
        url = site.get('url')
        selector = site.get('selector', 'a')
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
