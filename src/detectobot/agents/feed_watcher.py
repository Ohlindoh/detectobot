import feedparser
import yaml
import os
import sqlite3

from detectobot import feed_watcher as core

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config.yaml'))
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../feed_watcher.db'))

def load_config():
    """Load feed configuration from YAML file."""
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    feeds = [(feed['name'], feed['url']) for feed in config.get('feeds', [])]
    return feeds

def get_latest_article_links():
    """Return a list of dicts with 'name' and 'link' (latest article) for each feed."""
    feeds = load_config()
    latest_articles = []
    for name, url in feeds:
        feed = feedparser.parse(url)
        if feed.entries:
            entry = feed.entries[0]
            article_link = entry.get('link')
            if article_link:
                latest_articles.append({'name': name, 'link': article_link})
    return latest_articles


def get_new_article_links(db_path: str = DB_PATH):
    """Return unseen article links for all configured feeds."""
    feeds = load_config()
    conn = sqlite3.connect(db_path)
    core.init_db(conn)
    new_articles = []

    for name, url in feeds:
        feed = feedparser.parse(url)
        for entry in getattr(feed, "entries", []):
            h = core.entry_hash(entry)
            if core.check_and_store(conn, h, name, entry):
                link = entry.get("link")
                if link:
                    new_articles.append({"name": name, "link": link})

    conn.close()
    return new_articles

if __name__ == "__main__":
    for item in get_latest_article_links():
        print(f"--- {item['name']} ---\n- {item['link']}\n")
