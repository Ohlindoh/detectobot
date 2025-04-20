import feedparser
import yaml
import os

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config.yaml'))

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

if __name__ == "__main__":
    for item in get_latest_article_links():
        print(f"--- {item['name']} ---\n- {item['link']}\n")
