import feedparser
import yaml
import os

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config.yaml'))

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    feeds = [(feed['name'], feed['url']) for feed in config.get('feeds', [])]
    poll_interval = config.get('poll_interval_minutes', 60)
    return feeds, poll_interval

def get_latest_entries():
    feeds, poll_interval = load_config()
    latest_entries = []
    for name, url in feeds:
        feed = feedparser.parse(url)
        if feed.entries:
            entry = feed.entries[0]
            latest_entries.append({'name': name, 'url': url, 'entry': entry})
    return latest_entries

if __name__ == "__main__":
    for item in get_latest_entries():
        entry = item['entry']
        print(f"--- {item['name']} ---\n- {entry.get('title')} ({entry.get('link')})\n")
