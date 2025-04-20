import feedparser

FEEDS = [
    ("CISA Advisories", "https://www.cisa.gov/news-events/cybersecurity-advisories.xml"),
    ("Dark Reading", "https://www.darkreading.com/rss.xml"),
]

def main():
    for name, url in FEEDS:
        print(f"--- {name} ---")
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:  # Show top 5 entries
            print(f"- {entry.get('title')} ({entry.get('link')})")
        print()

if __name__ == "__main__":
    main()
